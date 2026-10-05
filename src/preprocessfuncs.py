import geopandas as gpd
import xarray as xr
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
