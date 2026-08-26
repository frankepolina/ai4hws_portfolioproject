
import geopandas as gpd

from importfuncs import import_hyras, import_sm_dwd

# _______________________________________________________________________________________________________________________
# Variable definition
# _______________________________________________________________________________________________________________________
study_area = gpd.read_file("./data/study_area.gpkg", layer="study_area")
study_box = study_area.geometry.iloc[0].bounds

start_year = 2014
end_year = 2019

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
    startyear=2014,
    endyear=2019,
    bbox=study_box,
    bboxCRS = study_area.crs
)

tasmax = import_hyras(
    variable="tasmax",
    startyear=2014,
    endyear=2019,
    bbox=study_box,
    bboxCRS = study_area.crs
)

sm_dwd_90_100 = import_sm_dwd(
    depth="90-100",
    startyear=2014,
    endyear=2019,
    bbox=study_box,
    bboxCRS=study_area.crs,   
)

sm_dwd_190_200 = import_sm_dwd(
    depth="190-200",
    startyear=2014,
    endyear=2019,
    bbox=study_box,
    bboxCRS=study_area.crs,   
)

# sm_cop = import_copernicus()



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