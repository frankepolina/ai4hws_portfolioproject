
import geopandas as gpd
import xarray as xr
from pathlib import Path

from importfuncs import import_hyras, import_sm_dwd
from preprocessfuncs import aggregate_by_region

# _______________________________________________________________________________________________________________________
# Variable definition
# _______________________________________________________________________________________________________________________
study_area = gpd.read_file("./data/study_area.gpkg", layer="study_area")
study_box = study_area.geometry.iloc[0].bounds

start_year = 2001
end_year = 2025

naturraum = gpd.read_file("../data/brandenburg_shape/naturraum_scholz_ohne_Berlin.gpkg", layer="naturraum_scholz_ohne_berlin")
naturraum_3035 = naturraum.to_crs("EPSG:3035")

pr_da = xr.open_dataset(Path("../data/imported")/"hyras_pr_v6-1_2001_2025.nc")["pr"]


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
# Preprocess (calculate features)
# _______________________________________________________________________________________________________________________

# pr = calculate_pr_anomalies(pr)

# tas = ...

# _______________________________________________________________________________________________________________________
# Build feature dataset
# _______________________________________________________________________________________________________________________

# features = build_feat_dataset()

# _______________________________________________________________________________________________________________________
# ML/Clustering
# _______________________________________________________________________________________________________________________

# ...