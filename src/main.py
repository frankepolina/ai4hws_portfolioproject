
import geopandas as gpd
import xarray as xr
from pathlib import Path

from importfuncs import import_hyras, import_sm_dwd
from preprocessfuncs import aggregate_to_naturraeume, aggregate_to_dekad, calc_dekad_climatology

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
pr_sum = aggregate_to_dekad("pr",
                            "sum",
                            "./data/processed/pr_spatial_agg_natraum_2001_2025.nc",
                            start_year,
                            end_year)

tas_mean = aggregate_to_dekad("tas",
                              "mean",
                              "./data/processed/tas_spatial_agg_natraum_2001_2025.nc",
                              start_year,
                              end_year)

tasmin_min = aggregate_to_dekad("tasmin",
                                "min",
                                "./data/processed/tasmin_spatial_agg_natraum_2001_2025.nc",
                                start_year,
                                end_year)

tasmax_max = aggregate_to_dekad("tasmax",
                                "max",
                                "./data/processed/tasmax_spatial_agg_natraum_2001_2025.nc",
                                start_year,
                                end_year)

sm_top_mean = aggregate_to_dekad("sm_dwd_0_10",
                                 "mean",
                                 "./data/processed/sm_dwd_0_10_spatial_agg_natraum_2001_2025.nc",
                                 start_year,
                                 end_year)

sm_mid_mean = aggregate_to_dekad("sm_dwd_90_100",
                                 "mean",
                                 "./data/processed/sm_dwd_90_100_spatial_agg_natraum_2001_2025.nc",
                                 start_year,
                                 end_year)

sm_low_mean = aggregate_to_dekad("sm_dwd_190_200",
                                 "mean",
                                 "./data/processed/sm_dwd_190_200_spatial_agg_natraum_2001_2025.nc",
                                 start_year,
                                 end_year)



# _______________________________________________________________________________________________________________________
# Compute Climatology
# _______________________________________________________________________________________________________________________
pr_clima = calc_dekad_climatology("pr",
                                  "./data/processed/pr_sum_dekadal_natraum_2001_2025.nc",
                                  start_year,
                                  end_year)

tas_clima = calc_dekad_climatology("tas",
                                   "./data/processed/tas_mean_dekadal_natraum_2001_2025.nc",
                                   start_year,
                                   end_year)

tasmin_clima = calc_dekad_climatology("tasmin",
                                      "./data/processed/tasmin_min_dekadal_natraum_2001_2025.nc",
                                      start_year,
                                      end_year)

tasmax_clima = calc_dekad_climatology("tasmax",
                                      "./data/processed/tasmax_max_dekadal_natraum_2001_2025.nc",
                                      start_year,
                                      end_year)

sw_top_clima = calc_dekad_climatology("sw_dwd_0_10",
                                      "./data/processed/sm_dwd_0_10_mean_dekadal_natraum_2001_2025.nc",
                                      start_year,
                                      end_year)

sw_mid_clima = calc_dekad_climatology("sw_dwd_90_100",
                                      "./data/processed/sm_dwd_90_100_mean_dekadal_natraum_2001_2025.nc",
                                      start_year,
                                      end_year)

sw_low_clima = calc_dekad_climatology("sw_dwd_190_200",
                                      "./data/processed/sm_dwd_190_200_mean_dekadal_natraum_2001_2025.nc",
                                      start_year,
                                      end_year)



# _______________________________________________________________________________________________________________________
# Build feature dataset
# _______________________________________________________________________________________________________________________

# features = build_feat_dataset()

# _______________________________________________________________________________________________________________________
# ML/Clustering
# _______________________________________________________________________________________________________________________

# ...