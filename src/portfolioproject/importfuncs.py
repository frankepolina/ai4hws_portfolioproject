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
HYRAS_CRS = "EPSG_3035"

BASE_URL = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de"

# _______________________________________________________________________________________________________________________
# Helper functions
# _______________________________________________________________________________________________________________________

def _load_hyras_year(year, variable, bbox):
    """"
    Download, crop and load one HYRAS variable from DWD per one year 
    Inputs: year (int), variable [str], bbox [tuple] in EPSG:3035 (xmin,ymin,xmax,ymax)
    Return: xarray.DataArray
    """
    config = HYRAS_VARIABLES[variable]

    filename = config["filename"].format(year=year)

    url = (f"{BASE_URL}/{config['directory']}/{filename}")

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
            # normalize timesteps
            da = da.assign_coords(time=da.time.values.astype("datetime64[D]"))
            # load tempfile into memory
            da = da.load()

            return da



# _______________________________________________________________________________________________________________________
# import functions
# _______________________________________________________________________________________________________________________

def import_hyras(variable, startyear, endyear, bbox, bboxCRS="EPSG:3035"):
    """"
    Import one selected HYRAS variable from DWD for study period (startyear-endyear) and study area (bbox
    Inputs: variable [str], startyear/endyear [int], bbox [tuple] as xmin,ymin,xmax,ymax , bboxCRS [str], (default EPSG:3035)
    Return: xarray.DataArray
    """
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

    # sort time
    data = data.sortby("time")

    return data


