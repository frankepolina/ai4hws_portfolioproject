import geopandas as gpd
import xarray as xr
from pathlib import Path

from shapely.geometry import Point


# _______________________________________________________________________________________________________________________
# Variable definition
# _______________________________________________________________________________________________________________________


# _______________________________________________________________________________________________________________________


def aggregate_to_naturraeume(variable, data_array, grid_naturraum_3035, has_unique_reg_id=True, data_dir = "./data/processed") -> xr.DataArray:
    """
    Aggregate a gridded DataArray to Naturraum (Scholz, 1962) regions.
    Each grid cell is assigned to the Naturraum polygon containing its grid-cell centre. 
    The function then calculates the spatial mean for each Naturraum region.

    Input:
    - data_array: xarray.DataArray to be aggregated with dimensions ("time", "y", "x").
    - grid_naturraum_3035: geopandas.GeoDataFrame containing a unique region_id for each grid cell, should be in EPSG:3035.
    - has_unique_reg_id: bool, default=True. Does the grid_naturraum GeoDataFrame contain a unique polygon identified (e.g. fid). 
      If False, a unique polygon identifier is created.
    
    Return:
    - xr.DataArray of aggregated data array with mean values for each unique region with dimensions ("time","region_id").

    
    Scholz, E. (1962): Die naturräumliche Gliederung Brandenburgs. Pädagogisches Bezirkskabinett, Potsdam, 71 p.
    """
    # check if aggregated data file exists
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    out_file = (data_dir / f"{variable}_spatial_agg_naturraum")

    # create unique polygon id, if False
    if not has_unique_reg_id:
        natraum_3035 = grid_naturraum_3035.copy()
        natraum_3035["region_id"] = range(len(natraum_3035))
    
    elif "region_id" not in natraum_3035.columns:
            raise ValueError(f"has_unique_reg_id=True, but 'region_id' is not present in {natraum_3035}.")

    # grid cell centre look up table (code by ChatGPT)
    x, y = xr.broadcast(da.x, da.y)
    grid_points = gpd.GeoDataFrame(
        {
            "x": x.values.ravel(),
            "y": y.values.ravel(),
        },
        geometry=[
            Point(xi, yi)
            for xi, yi in zip(x.values.ravel(), y.values.ravel())
        ],
        crs="EPSG:3035",
    )

    # assign each grid centre to a polygon
    grid_natraum = gpd.sjoin(
        grid_points,
        natraum_3035[
            [
                "region_id",
                "NR_HAUPT",
                "NAME_HAUPT",
                "NR_UNTER",
                "NAME_UNTER",
                "AREA",
                "geometry",
            ]
        ],
        how="left",
        predicate="within",
    )    

    # reshape back to 2D array
    region_ids = grid_natraum["region_id"].to_numpy()
    region_ids = region_ids.reshape(len(data_array.y), len(data_array.x))
    region_id_da = xr.DataArray(region_ids, dims=("y", "x"), coords={"y": data_array.y, "x": data_array.x}, name="region_id")

    # aggregate to naturraum polygons 
    da_agg = data_array.groupby(region_id_da).mean(dim="stacked_y_x")

    return da_agg
