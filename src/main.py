
import geopandas as gpd
import xarray as xr
from pathlib import Path

from importfuncs import import_hyras, import_sm_dwd
from preprocessfuncs import aggregate_to_naturraeume, aggregate_to_dekad, calc_dekad_climatology
from featurefuncs import compute_diurnal_range, compute_dry_days, compute_sm_3dekad_trend, compute_precip_3dekad_rollsum, standardize_anomaly, assemble_feature_dataset

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



# recalculate pr dekad with log1p transformation, to account for right-skewedness 
pr_log_clima = calc_dekad_climatology("pr",
                                  "./data/processed/pr_sum_dekadal_natraum_2001_2025.nc",
                                  start_year,
                                  end_year,
                                  logtransform=True,
                                  overwrite=True)
print(pr_log_clima.attrs)           # logtransform should be 1
print(float(pr_log_clima["mean"].min()), float(pr_log_clima["mean"].max())) # expectin values between around 2 - 3.5 (log1p(6) and log1p(37))



# _______________________________________________________________________________________________________________________
# Build feature dataset
# _______________________________________________________________________________________________________________________

# diurnal range calculated from daily temps

dtr_daily = compute_diurnal_range(tasmax_daily="./data/processed/tasmax_spatial_agg_natraum_2001_2025.nc",
                                          tasmin_daily="./data/processed/tasmin_spatial_agg_natraum_2001_2025.nc",
                                          out_path="./data/processed/dailydiurnalrange_spatial_agg_natraum_2001_2025.nc")

# dekadal mean of diurnal range

dtr_mean = aggregate_to_dekad(variable="dtr",
                              aggregation="mean",
                              data_array_path="./data/processed/dailydiurnalrange_spatial_agg_natraum_2001_2025.nc",
                              startyear=start_year,
                              endyear=end_year)
                           
# climatology of dtr

dtr_clima = calc_dekad_climatology(variable="dtr",
                                   data_array_path="./data/processed/dtr_mean_dekadal_natraum_2001_2025.nc",
                                   startyear=start_year,
                                   endyear=end_year)


# dry days count per dekad (allready agg to dekad)

drydays = compute_dry_days(pr_daily="./data/processed/pr_spatial_agg_natraum_2001_2025.nc",
                           out_path="./data/processed/drydays_dekadal_natraum_2001_2025.nc",
                           threshold=1.0)

# climatology for drydays

drydays_clim = calc_dekad_climatology(variable="drydays",
                                 data_array_path="./data/processed/drydays_dekadal_natraum_2001_2025.nc",
                                 startyear=2001, endyear=2025)


# pr 3dekad rolling sum 

pr3dek = compute_precip_3dekad_rollsum(pr_dekad="./data/processed/pr_sum_dekadal_natraum_2001_2025.nc",
                                       out_path="./data/processed/pr3dekad_sum_natraum_2001_2025.nc")

# climatology for pr3dek
pr3dek_clima = calc_dekad_climatology(variable="pr3dekad",
                                  data_array_path="./data/processed/pr3dekad_sum_natraum_2001_2025.nc",
                                  startyear=2001, endyear=2025,
                                  logtransform=True)

# sm top 3 dekad trend
smtop_trend = compute_sm_3dekad_trend(sm_dekad="./data/processed/sm_dwd_0_10_mean_dekadal_natraum_2001_2025.nc",
                                      out_path="./data/processed/smtop_trend_dekadal_natraum_2001_2025.nc")

# sm trend climatology
smtop_trend_clima = calc_dekad_climatology(variable="smtop_trend",
                                           data_array_path="./data/processed/smtop_trend_dekadal_natraum_2001_2025.nc",
                                           startyear=2001, endyear=2025)

# all 9 features are standardized:

tas_z = standardize_anomaly(data="./data/processed/tas_mean_dekadal_natraum_2001_2025.nc",
                            climatology="./data/processed/tas_dekad_climatology_natraum_2001_2025.nc",
                            feature_name="tas_z")

smtop_z = standardize_anomaly(data="./data/processed/sm_dwd_0_10_mean_dekadal_natraum_2001_2025.nc",
                            climatology="./data/processed/sm_dwd_0_10_dekad_climatology_natraum_2001_2025.nc",
                            feature_name="smtop_z")
smmid_z = standardize_anomaly(data="./data/processed/sm_dwd_90_100_mean_dekadal_natraum_2001_2025.nc",
                            climatology="./data/processed/sm_dwd_90_100_dekad_climatology_natraum_2001_2025.nc",
                            feature_name="smmid_z")
smlow_z = standardize_anomaly(data="./data/processed/sm_dwd_190_200_mean_dekadal_natraum_2001_2025.nc",
                            climatology="./data/processed/sm_dwd_190_200_dekad_climatology_natraum_2001_2025.nc",
                            feature_name="smlow_z")

pr_z = standardize_anomaly(data="./data/processed/pr_sum_dekadal_natraum_2001_2025.nc",
                           climatology="./data/processed/pr_log1p_dekad_climatology_natraum_2001_2025.nc",
                           feature_name="pr_z", overwrite=True)

dtr_z = standardize_anomaly(data="./data/processed/dtr_mean_dekadal_natraum_2001_2025.nc",
                            climatology="./data/processed/dtr_dekad_climatology_natraum_2001_2025.nc",
                            feature_name="dtr_z")

drydays_z = standardize_anomaly(data="./data/processed/drydays_dekadal_natraum_2001_2025.nc",
                                climatology=drydays_clim,
                                feature_name="drydays_z")

pr3dek_z = standardize_anomaly(data="./data/processed/pr3dekad_sum_natraum_2001_2025.nc",
                             climatology=pr3dek_clima,
                             feature_name="pr3dek_z")

smtop_trend_z = standardize_anomaly(data="./data/processed/smtop_trend_dekadal_natraum_2001_2025.nc",
                                    climatology=smtop_trend_clima,
                                    feature_name="smtop_trend_z")


# create one feature ds
feature_ds = assemble_feature_dataset("./data/features")




# _______________________________________________________________________________________________________________________
# ML/Clustering
# _______________________________________________________________________________________________________________________

# had to run the rest in a notebook, due to time constrains :/
# see dev/explore_features.ipynb and dev/analysis_features_clusters.ipynb