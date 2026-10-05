import geopandas as gpd
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path


# _______________________________________________________________________________________________________________________
# Variable definition
# _______________________________________________________________________________________________________________________


# _______________________________________________________________________________________________________________________


def aggregate_to_naturraeume(variable, startyear, endyear, data_array_path, cell_center_grid_naturraum, gridCRS, has_unique_reg_id=True, data_dir = "./data/processed") -> xr.DataArray:
    """
    Aggregate a gridded DataArray to Naturraum (Scholz, 1962) regions.
    Each grid cell is assigned to the Naturraum polygon containing its grid-cell centre. 
    The function then calculates the spatial mean for each Naturraum region.

    Input:
    - variable [str]: Name of variable to spatially aggregate
    - data_array_path [str]: Path to gridded data to be aggregated, must have dimensions ("time", "y", "x").
    - cell_center_grid_naturraum [str]: Path to cell center lookup table as Parquet file. 
        The table must contain one row per grid cell and a "region_id" column if has_unique_reg_id=True. 
    . gridCRS [str]: CRS of cell center lookup table, should be either EPSG:3035 for HYRAS or EPSG:31467 for DWD Soil Moisture.
    - has_unique_reg_id [bool]: default=True. Does the lookup table contain a unique polygon identifyer called 'region_id'? 
      If False, error is rased.
    
    Return:
    - xr.DataArray of aggregated data array with mean values for each unique region with dimensions ("time","region_id").

    
    Scholz, E. (1962): Die naturräumliche Gliederung Brandenburgs. Pädagogisches Bezirkskabinett, Potsdam, 71 p.
    """
    # set output dir and check if aggregated data file already exists
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = (data_dir / f"{variable}_spatial_agg_natraum_{startyear}_{endyear}.nc")
    if out_file.exists():
        print(f"(Dataset already exists. Loading cached {variable} data: {out_file})")
        return xr.open_dataarray(out_file)

    data_array = xr.open_dataset(Path(data_array_path))[variable]
    
    # check if gridCRS is in correct EPSG
    if gridCRS not in ["EPSG:3035", "EPSG:31467"]:
        raise ValueError(f"Expected EPSG:3035 or EPSG:31467 for gridCRS, but got {gridCRS}.")
    
    # check input dimensions
    required_dims = {"time", "y", "x"}
    if not required_dims.issubset(data_array.dims):
        raise ValueError(f"data_array must contain dimensions {required_dims}, but has {data_array.dims}.")


    # load grid cell lookup table
    lookup_file = Path(cell_center_grid_naturraum)

    if not lookup_file.exists():
         raise FileNotFoundError(f"Naturraum grid lookup table not found: {lookup_file}")

    grid_natraum = gpd.read_parquet(lookup_file)

    # check for region_id
    if has_unique_reg_id:
        if "region_id" not in grid_natraum.columns:
             raise ValueError(f"has_unique_reg_id=True, but 'region_id' not found in {cell_center_grid_naturraum}")
    else: raise ValueError(f"has_unique_reg_id=False not supported yet... Sorry!! Please create uniqure region_id when constructing lookup table.")

    # convert lookup to 2D array
    region_ids = grid_natraum["region_id"].to_numpy()

    region_ids = region_ids.reshape(len(data_array.y), len(data_array.x))
    region_id_da = xr.DataArray(
        region_ids,
        dims=("y", "x"),
        coords={
            "y": data_array.y,
            "x": data_array.x
        },
        name="region_id"
        )

    # aggregate to naturraum polygons 
    da_agg = data_array.groupby(region_id_da).mean(dim="stacked_y_x")

    # save aggregated data
    print(f"Saving spatially aggregated {variable} data to: {out_file}")
    da_agg.to_netcdf(out_file)

    return da_agg



def aggregate_to_dekad(variable, aggregation, data_array_path, startyear, endyear, data_dir="./data/processed"):
    """
    Aggregate daily gridded data to calendar-based dekads, as defined by WMO standard.
    Dekad 1: days 1-10, dekad 2: days 11-20, dekad 3: days 21-end of month.

    Inputs:
    - variable [str]: Name of variable in the NetCDF file.
    - aggregation [str]: {"mean", "sum", "min", "max"} aggregation method.
    - data_array_path: Path to input file
    - startyear [int]: First year of input period, only used for naming convention.
    - endyear [int]: Last year of input period, only used for naming convention.
    - data_dir: Path to directory for aggregated output, default="./data/processed".

    Returns:
    - xarray.DataArray:dekadal aggregated data with dimensions (region_id, year, month, dekad)
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    out_file = (data_dir / f"{variable}_{aggregation}_dekadal_natraum_{startyear}_{endyear}.nc")

    if out_file.exists():
        print(f"Dataset already exists. Loading cached data: {out_file}")
        return xr.open_dataarray(out_file)

    # Load daily data
    da = xr.open_dataarray(data_array_path)

    # Create calendar dekad identifiers
    dates = pd.DatetimeIndex(da.time.values)
    
    dekad_of_month = np.where(dates.day <= 10, 1,
                          np.where(dates.day <= 20, 2, 3)
                          )

    # add year, month, dekad as coordinates
    da = da.assign_coords(
        year=("time", dates.year),
        month=("time", dates.month),
        dekad=("time", dekad_of_month),
    )

    # aggregate daily to dekadal
    da_grouped = da.groupby(["year", "month", "dekad"])

    if aggregation == "mean":
        da_dekadal = da_grouped.mean(dim="time")
    elif aggregation == "sum":
        da_dekadal = da_grouped.sum(dim="time")
    elif aggregation == "min":
        da_dekadal = da_grouped.min(dim="time")
    elif aggregation == "max":
        da_dekadal = da_grouped.max(dim="time")
    else:
        raise ValueError(f"Invalid aggregation '{aggregation}'. Choose one of the following: mean, sum, min, max ")

    # save
    print(f"Saving dekadal {aggregation} {variable} data to: {out_file}")
    da_dekadal.to_netcdf(out_file)

    return da_dekadal



def calc_dekad_climatology(variable, data_array_path, startyear, endyear, data_dir="./data/processed"):
    """
    Calculate calendar-dekad climatology from dekadally aggregated data.
    For each Naturraum, month and dekad the mean and standard deviation across all years are calculated. 

    Inputs:
    - variable [str]: Name of variable in the NetCDF file.
    - data_array_path: Path to dekadally aggregated NetCDF file.
    - startyear [int]: First year of input period, only used for naming convention.
    - endyear [int]: Last year of input period, only used for naming convention.
    - data_dir: Path to directory for output, default="./data/processed".

    Returns:
    - xarray.Dataset containing:
        - mean: climatological mean
        - std: climatological standard deviation
        Dimensions:
        (region_id, month, dekad)

    """

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    out_file = (data_dir / f"{variable}_dekad_climatology_natraum_{startyear}_{endyear}.nc")

    if out_file.exists():
        print(f"Dataset already exists. Loading cached climatology: {out_file}")
        return xr.open_dataset(out_file)

    da = xr.open_dataarray(data_array_path)

    # check required dims
    required_dims = {"year", "month", "dekad", "region_id"}
    missing_dims = required_dims - set(da.dims)

    if missing_dims:
        raise ValueError(f"Input DataArray is missing required dimensions: {missing_dims}")
    
    # calculate mean and std
    climatology_mean = da.mean(dim="year")
    climatology_std = da.std(dim="year")
    climatology_n = da.count(dim="year")

    # save mean and std in same dataset
    climatology = xr.Dataset({"mean": climatology_mean, "std": climatology_std, "n_years": climatology_n})

    # check for std of zero
    n_zero_std = int((climatology_std == 0).sum())
    if n_zero_std > 0:
        print(f"WARNING: {n_zero_std} (region, month, dekad) polygons have zero std for {variable}.")

    # check for any missing years
    min_n = int(climatology_n.min())
    if min_n < endyear - startyear + 1:
        print(f"Note: some (region, month, dekad) polygons have fewer than {endyear - startyear + 1} valid years (min = {min_n}).")

    # add description for the forgetful brains... 
    climatology.attrs["description"] = (f"Calendar-dekad climatology for {variable}, calculated over {startyear}-{endyear}.")

    # save data set
    print(f"Saving {variable} dekadal climatology to: {out_file}")
    climatology.to_netcdf(out_file)

    return climatology



