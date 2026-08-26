import tempfile
import urllib.request
from pathlib import Path

import geopandas as gpd
import xarray as xr
from shapely.geometry import box

# _______________________________________________________________________________________________________________________
# Variable definition
# _______________________________________________________________________________________________________________________

HYRAS_VARIABLES = {"pr": {"directory": "precipitation", "filename": "pr_hyras_1_{year}_v6-1_de.nc"},
                   "tas": {"directory": "air_temperature_mean", "filename": "tas_hyras_1_{year}_v6-1_de.nc"},
                   "tasmax": {"directory": "air_temperature_max", "filename": "tasmax_hyras_1_{year}_v6-1_de.nc"}
                   }
HYRAS_CRS = "EPSG:3035"
HYRAS_BASE_URL = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de"


DWD_SM_DEPTHS = ["90-100", "190-200"]
DWD_SM_CRS = "EPSG:31467"
DWD_SM_BASE_URL = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/soil_moisture/composite"



# _______________________________________________________________________________________________________________________
# Helper functions
# _______________________________________________________________________________________________________________________

def _load_hyras_year(year, variable, bbox):
    """
    Download, crop and load one HYRAS variable from DWD per one year. 
    Inputs: year (int), variable [str], bbox [tuple] in EPSG:3035 (xmin,ymin,xmax,ymax)
    Return: xarray.DataArray
    """
    config = HYRAS_VARIABLES[variable]

    filename = config["filename"].format(year=year)

    url = (f"{HYRAS_BASE_URL}/{config['directory']}/{filename}")

    xmin,ymin,xmax,ymax = bbox

    with tempfile.TemporaryDirectory() as tmpdir:
        # configure path to variable
        local_file = Path(tmpdir) / filename
        # download variable
        print(f"Downloading {variable}: {filename}...")
        urllib.request.urlretrieve(url, local_file)
        # open file
        with xr.open_dataset(local_file, engine="netcdf4") as ds:
            # crop to study area
            ds_region = ds.sel(x=slice(xmin,xmax), y=slice(ymin,ymax))
            # extract variable
            da = ds_region[variable]
            # normalize timesteps
            da = da.assign_coords(time=da.time.values.astype("datetime64[D]"))
            # load tempfile into memory
            da = da.load()

    return da


def _load_sm_dwd_year(year,depth, bbox):
    """
    Download, crop and load one DWD soil moisture depth layer as variable per one year. 
    Inputs: year (int), depth [str], e.g. "90-100", bbox [tuple] in EPSG:31467 (xmin,ymin,xmax,ymax)
    Return: xarray.DataArray
    """
    filename = f"grids_germany_daily_soil_moisture_composite_{year}_{depth}_v1.nc"

    url = f"{DWD_SM_BASE_URL}/{year}/{filename}"

    xmin,ymin,xmax,ymax = bbox

    with tempfile.TemporaryDirectory() as tmpdir:

        local_file = Path(tmpdir) / filename

        print(f"Downloading soil moisture {depth}: {filename}...")
        # check if this depth exists
        try:
            urllib.request.urlretrieve(url, local_file)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise FileNotFoundError(
                    f"No DWD soil-moisture file found for depth '{depth}' and year {year}.\n"
                    f"Expected file: {filename}\n"
                    f"URL: {url}"
                ) from e
            raise

        with xr.open_dataset(local_file, engine="netcdf4") as ds:
            # Sttention: soil-moisture y coordinate is descending!!
            ds_region = ds.sel(x=slice(xmin, xmax), y=slice(ymax, ymin))

            da = ds_region["paws"]

            # Remove length-1 layer dimension
            da = da.squeeze("lyr", drop=True)

            # Normalize time to daily dates
            da = da.assign_coords(time=da.time.values.astype("datetime64[D]"))

            # Load before temporary file is deleted
            da = da.load()

            return da 



# _______________________________________________________________________________________________________________________
# import functions
# _______________________________________________________________________________________________________________________

def import_hyras(variable, startyear, endyear, bbox, bboxCRS="EPSG:3035", data_dir = "./data/imported"):
    """
    Import one selected HYRAS variable from DWD for study period (startyear-endyear) and study area (bbox).
    Inputs: variable [str], startyear/endyear [int], bbox [tuple] as xmin,ymin,xmax,ymax , bboxCRS [str], (default "EPSG:3035")
    Return: xarray.DataArray
    """
    # check if data was already imported before
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    output_file = (data_dir / f"hyras_{variable}_v6-1_{startyear}_{endyear}.nc")

    if output_file.exists():
        print(f"Dataset already imported. Loading cached HYRAS data: {output_file}")
        return xr.open_dataarray(output_file)

    # check if correct variable name
    if variable not in HYRAS_VARIABLES:
        raise ValueError(f"Unknown HYRAS variable: '{variable}'. Variable must be one of the following: {list(HYRAS_VARIABLES)}.")

    # create GeoDataFrame for bbox
    bbox_gdf = gpd.GeoDataFrame(geometry=[box(*bbox)], crs=bboxCRS)
    # transform CRS to match hyras
    bbox_hyras = bbox_gdf.to_crs(HYRAS_CRS)
    # extract bounds
    hyras_bbox = bbox_hyras.total_bounds

    # load each year
    yearly_data = []

    for year in range(startyear,endyear+1):
        da = _load_hyras_year(year=year, variable=variable, bbox=hyras_bbox)

        yearly_data.append(da)
    # concat years along time-axis
    data = xr.concat(yearly_data, dim="time")

    # sort time in chronological order
    data = data.sortby("time")

    # save imported data as nc file
    print(f"Saving imported '{variable}' HYRAS data: {output_file}")
    data.to_netcdf(output_file)

    return data




def import_sm_dwd(depth, startyear, endyear, bbox, bboxCRS="EPSG:3035", data_dir = "./data/imported"):
    """
    Import for selected depth the DWD soil moisture composite for study period (startyear-endyear) and study area (bbox).
    Inputs: depth [str], startyear/endyear [int], bbox [tuple] as xmin,ymin,xmax,ymax , bboxCRS [str] of input bounding box, (default "EPSG:3035")
    Return: xarray.DataArray for specified depth and study period.
    """
    # check if data was already imported before
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    output_file = (data_dir / f"grids_germany_daily_soil_moisture_composite_{depth}_v1.nc")

    if output_file.exists():
        print(f"Dataset already imported. Loading cached DWD SM data: {output_file}")
        return xr.open_dataarray(output_file)

    # Create GeoDataFrame for bbox
    bbox_gdf = gpd.GeoDataFrame(geometry=[box(*bbox)], crs=bboxCRS)

    # Transform bbox to soil-moisture CRS
    bbox_sm = bbox_gdf.to_crs(DWD_SM_CRS)

    # Extract transformed bounds
    sm_bbox = bbox_sm.total_bounds

    # Load each year
    yearly_data = []

    for year in range(startyear, endyear+1):
        da = _load_sm_dwd_year(year=year, depth=depth, bbox=sm_bbox)

        yearly_data.append(da)

    # Concat years along time axis
    data = xr.concat(yearly_data, dim="time")

    # sort time
    data = data.sortby("time")

    # rename
    data.name = f"sm_dwd_{depth.replace('-','_')}"

    # store depth as metadata just in case
    data.attrs["soil_depth"] = depth

    # save imported data as nc file
    print(f"Saving imported DWD soil moisture data at '{depth}' depth: {output_file}")
    data.to_netcdf(output_file)

    return data


