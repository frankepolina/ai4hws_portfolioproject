
import geopandas as gpd
import xarray as xr
from pathlib import Path

from importfuncs import import_hyras, import_sm_dwd
from preprocessfuncs import aggregate_to_naturraeume

# _______________________________________________________________________________________________________________________
# Variable definition
# _______________________________________________________________________________________________________________________
study_area = gpd.read_file("./data/study_area.gpkg", layer="study_area")
study_box = study_area.geometry.iloc[0].bounds

start_year = 2001
end_year = 2025

lookup_hyras = "./data/processed/cell_centers_grid_naturraum_for_hyras.parquet"
lookup_dwdsm = "./data/processed/cell_centers_grid_naturraum_for_sm.parquet"

hyrasCRS = "EPSG:3035"
dwdsmCRS = "EPSG:31467"

# _______________________________________________________________________________________________________________________
# Import data
# _______________________________________________________________________________________________________________________
"""

pr = import_hyras(
    variable="pr",
    startyear=start_year,
    endyear=end_year,
    bbox=study_box,
    bboxCRS = study_area.crs
)

tas = import_hyras(    
    variable="tas",
    startyear=start_year,
    endyear=end_year,
    bbox=study_box,
    bboxCRS = study_area.crs
)

tasmax = import_hyras(
    variable="tasmax",
    startyear=start_year,
    endyear=end_year,
    bbox=study_box,
    bboxCRS = study_area.crs
)

tasmin = import_hyras(
    variable="tasmin",
    startyear=start_year,
    endyear=end_year,
    bbox=study_box,
    bboxCRS = study_area.crs
)

sm_dwd_0_10 = import_sm_dwd(
    depth="0-10",
    startyear=start_year,
    endyear=end_year,
    bbox=study_box,
    bboxCRS=study_area.crs,   
)

sm_dwd_90_100 = import_sm_dwd(
    depth="90-100",
    startyear=start_year,
    endyear=end_year,
    bbox=study_box,
    bboxCRS=study_area.crs,   
)

sm_dwd_190_200 = import_sm_dwd(
    depth="190-200",
    startyear=start_year,
    endyear=end_year,
    bbox=study_box,
    bboxCRS=study_area.crs,   
)

"""

# _______________________________________________________________________________________________________________________
# Preprocess 
# _______________________________________________________________________________________________________________________
# Spatial Aggregation to Naturraum Polygons
pr_natraum_daily = aggregate_to_naturraeume(variable="pr",
                                            startyear=start_year,
                                            endyear=end_year,
                                            data_array_path="./data/imported/hyras_pr_v6-1_2001_2025.nc",
                                            cell_center_grid_naturraum=lookup_hyras,
                                            gridCRS=hyrasCRS,
                                            has_unique_reg_id=True)


tas_natraum_daily = aggregate_to_naturraeume(variable="tas",
                                             startyear=start_year,
                                             endyear=end_year,
                                             data_array_path="./data/imported/hyras_tas_v6-1_2001_2025.nc",
                                             cell_center_grid_naturraum=lookup_hyras,
                                             gridCRS=hyrasCRS,
                                             has_unique_reg_id=True)

tasmin_natraum_daily = aggregate_to_naturraeume(variable="tasmin",
                                             startyear=start_year,
                                             endyear=end_year,
                                             data_array_path="./data/imported/hyras_tasmin_v6-1_2001_2025.nc",
                                             cell_center_grid_naturraum=lookup_hyras,
                                             gridCRS=hyrasCRS,
                                             has_unique_reg_id=True)

tasmax_natraum_daily = aggregate_to_naturraeume(variable="tasmax",
                                             startyear=start_year,
                                             endyear=end_year,
                                             data_array_path="./data/imported/hyras_tasmax_v6-1_2001_2025.nc",
                                             cell_center_grid_naturraum=lookup_hyras,
                                             gridCRS=hyrasCRS,
                                             has_unique_reg_id=True)

sm_top_natraum_daily = aggregate_to_naturraeume(variable="sm_dwd_0_10",
                                             startyear=start_year,
                                             endyear=end_year,
                                             data_array_path="./data/imported/grids_germany_daily_soil_moisture_composite_0-10_v1.nc",
                                             cell_center_grid_naturraum=lookup_dwdsm,
                                             gridCRS=dwdsmCRS,
                                             has_unique_reg_id=True)

sm_mid_natraum_daily = aggregate_to_naturraeume(variable="sm_dwd_90_100",
                                             startyear=start_year,
                                             endyear=end_year,
                                             data_array_path="./data/imported/grids_germany_daily_soil_moisture_composite_90-100_v1.nc",
                                             cell_center_grid_naturraum=lookup_dwdsm,
                                             gridCRS=dwdsmCRS,
                                             has_unique_reg_id=True)

sm_low_natraum_daily = aggregate_to_naturraeume(variable="sm_dwd_190_200",
                                             startyear=start_year,
                                             endyear=end_year,
                                             data_array_path="./data/imported/grids_germany_daily_soil_moisture_composite_190-200_v1.nc",
                                             cell_center_grid_naturraum=lookup_dwdsm,
                                             gridCRS=dwdsmCRS,
                                             has_unique_reg_id=True)

# Temporal Aggregation to Dekadal

# _______________________________________________________________________________________________________________________
# Build feature dataset
# _______________________________________________________________________________________________________________________

# features = build_feat_dataset()

# _______________________________________________________________________________________________________________________
# ML/Clustering
# _______________________________________________________________________________________________________________________

# ...