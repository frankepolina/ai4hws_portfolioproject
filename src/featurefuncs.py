import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
from pathlib import Path


# _______________________________________________________________________________________________________________________
# Variable Definition
# _______________________________________________________________________________________________________________________

FEATURE_NAMES = ["pr_z", "pr3dek_z", "drydays_z", "tas_z", "dtr_z", "smtop_z", "smtop_trend_z", "smmid_z", "smlow_z"]

# _______________________________________________________________________________________________________________________
# Helper functions
# _______________________________________________________________________________________________________________________

def _load_dataarray(path):
    """
    Load a NetCDF file as an xarray DataArray.
    """
    with xr.open_dataarray(path) as da:
        return da.load()


def _load_climatology(path):
    """
    Load a climatology NetCDF file as an xarray Dataset.
    """
    with xr.open_dataset(path) as ds:
        return ds.load()

def _fix_region_dtype(obj):
    """
    Cast region_id to int so alignment can't silently fail on float/int mismatch.
    Note: code for this function by ChatGPT, fixed a region_id type error.
    """
    return obj.assign_coords(region_id=obj["region_id"].astype(int))

# _______________________________________________________________________________________________________________________
# Variable-Specific Processing
# _______________________________________________________________________________________________________________________

def compute_diurnal_range(tasmax_daily, tasmin_daily, out_path, overwrite=False):
    """
    
    """
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        print(f"Loading cached daily DTR: {out_path}")
        return _load_dataarray(out_path)

    tasmax_daily = _load_dataarray(tasmax_daily)
    tasmin_daily = _load_dataarray(tasmin_daily)

    tmax = _fix_region_dtype(tasmax_daily)
    tmin = _fix_region_dtype(tasmin_daily)

    # join="exact" raises an error if coordinates differ, instead of silently dropping mismatched days
    tmax, tmin = xr.align(tmax, tmin, join="exact")

    # calculate diurnal range (max-min)
    dtr = tmax - tmin
    dtr.name = "dtr"

    if float(dtr.min()) < 0:
        raise ValueError(f"Negative diurnal range found (min = {float(dtr.min()):.2f}), tasmax/tasmin may be swapped or misaligned.")

    dtr.attrs.update({
        "long_name": "Daily diurnal temperature range (tasmax - tasmin)",
        "units": "degree_Celsius",
    })
    
    print(f"Saving daily DTR to: {out_path}")
    dtr.to_netcdf(out_path)

    return dtr



def compute_dry_days(pr_daily, out_path, threshold=1.0, overwrite=False):

    """
    Count of dry days (< 1 mm prcp/day) per dekad and Naturraum.
    
    Inputs:
    - pr_daily: Path or xr.DataArray of daily precipitation (mm) per Naturraum,
                dims (time, region_id).
    - out_path: output NetCDF path.
    - threshold [float]: dry-day threshold in mm, default 1.0.
    
    Note: function already computes temporal aggregation sum!

    Returns:
    - xr.DataArray, dims (region_id, year, month, dekad), values = dry-day count per dekad.
    """
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        print(f"Loading cached dry-day counts: {out_path}")
        return _load_dataarray(out_path)
    
    if isinstance(pr_daily, (str, Path)):
        pr_daily = _load_dataarray(pr_daily)
    pr = _fix_region_dtype(pr_daily)

    if float(pr.min()) < 0:
        raise ValueError("Negative precipitation values found.")

    # dry-day log
    # keep NaN where pr is missing instead of counting it as wet
    dry = (pr < threshold).astype(float).where(pr.notnull())

    dates = pd.DatetimeIndex(pr["time"].values)
    dekad_of_month = np.where(dates.day <= 10, 1, np.where(dates.day <= 20, 2, 3))

    dry = dry.assign_coords(
        year=("time", dates.year),
        month=("time", dates.month),
        dekad=("time", dekad_of_month),
    )

    counts = dry.groupby(["year", "month", "dekad"]).sum(dim="time", skipna=True, min_count=1)
    counts = counts.transpose("region_id", "year", "month", "dekad")    

    counts.name = "drydays"
    counts.attrs.update({
        "long_name": f"Dry days per dekad (daily precipitation < {threshold} mm)",
        "units": "days",
        "threshold_mm": threshold,
    })

    print(f"Saving dry-day counts to: {out_path}")
    counts.to_netcdf(out_path)

    return counts



def compute_precip_3dekad_rollsum(pr_dekad, out_path, overwrite=False):
    """
    Rolling 3-dekad (~30-day) precipitation sum per Naturraum, in mm.
    The window ends on the current dekad and covers it plus the two preceding dekads,
    crossing month and year boundaries. 
    
    Note: No log transform here, that happens in calc_dekad_climatology / compute_anomaly (logtransform=True)

    Input:

    Return:


    """
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        print(f"Loading cached 3-dekad sums: {out_path}")
        return _load_dataarray(out_path)

    if isinstance(pr_dekad, (str, Path)):
        pr_dekad = _load_dataarray(pr_dekad)
    pr = _fix_region_dtype(pr_dekad).transpose("region_id", "year", "month", "dekad")

    # stack to one chronological axis; year is the outermost level, so order = time order
    stacked = pr.stack(t=("year", "month", "dekad"))
    if not stacked.indexes["t"].is_monotonic_increasing:
        raise ValueError("Stacked time axis is not chronological.")

    # require all 3 dekads in the window, otherwise NaN
    rolled = stacked.rolling(t=3, min_periods=3).sum()

    pr3 = rolled.unstack("t").transpose("region_id", "year", "month", "dekad")
    pr3.name = "pr3dekad"
    pr3.attrs.update({
        "long_name": "Precipitation sum over the current and two preceding dekads",
        "units": "mm",
    })

    print(f"Saving 3-dekad precipitation sums to: {out_path}")
    pr3.to_netcdf(out_path)
    return pr3


def compute_sm_3dekad_trend(sm_dekad, out_path, lag=3, overwrite=False):
    """
    Soil-moisture trend: SM(t) - SM(t - lag dekads), on a continuous chronological dekad axis
    (crosses month and year boundaries). lag=3 is roughly 30 days.
    Positive = wetting, negative = drying. Units are those of the input data.

    Input:
    - sm_dekad: path or xr.DataArray of dekadal mean soil moisture, with dims (region_id, year, month, dekad).
    
    Output:
    - xr.DataArray, same dims; the first `lag` dekads of the record are NaN.

    """
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        print(f"Loading cached SM trend: {out_path}")
        return _load_dataarray(out_path)

    if isinstance(sm_dekad, (str, Path)):
        sm_dekad = _load_dataarray(sm_dekad)

    sm = _fix_region_dtype(sm_dekad).transpose("region_id", "year", "month", "dekad")

    stacked = sm.stack(t=("year", "month", "dekad"))
    if not stacked.indexes["t"].is_monotonic_increasing:
        raise ValueError("Stacked time axis is not chronological.")
    # shift() is positional, so the grid must be complete (36 dekads in every year)
    if stacked.sizes["t"] != sm.sizes["year"] * 36:
        raise ValueError("Incomplete dekad grid, the lagged difference would be misaligned.")

    trend = stacked - stacked.shift(t=lag)

    trend = trend.unstack("t").transpose("region_id", "year", "month", "dekad")
    trend.name = "smtop_trend"
    trend.attrs.update({
        "long_name": f"Soil moisture change over {lag} dekads: SM(t) - SM(t-{lag})",
        "units": sm.attrs.get("units", "same as input"),
    })

    print(f"Saving SM top trend to: {out_path}")
    trend.to_netcdf(out_path)

    return trend


# _______________________________________________________________________________________________________________________
# Feature calculation functions
# _______________________________________________________________________________________________________________________

def compute_anomaly(data, climatology):
    """
    Function computes anomalies relative to calendar-dekad climatological mean.

    Inputs:
    - data: xr.DataArray with dekadal values and dimensions ("region_id", "year", "month", "dekad").
    - climatology: xr.Dataset containing "mean" and "std" with dimensions ("region_id", "month", "dekad").

    Return:
    xr.DataArray with anomalies in same units as data.

    """

    data = _fix_region_dtype(data)
    clima = _fix_region_dtype(climatology)

    if "mean" not in climatology:
        raise ValueError("Climatology must contain a 'mean' variable.")

    if int(climatology.attrs.get("logtransform", 0)) == 1:
        if float(data.min()) < 0:
            raise ValueError("Negative values found, but log1p is not defined for values < -1.")
        data = np.log1p(data)
        print(f"{data} was log1p-transformed...")
    
    anomaly = data - clima["mean"]
    anomaly.name = f"{data.name or 'variable'}_anom"

    return anomaly


def standardize_anomaly(data, climatology, feature_name, data_dir="./data/features", overwrite=False):

    """
    Standardize climatological anomaly data. 
    Climatology must be calculated in same data space as input data,
    e.g. raw or log-transformed, and contain mean and std values. 

    Note: Values of 0 std besome NaN instead of inf. 

    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    out_file = data_dir / f"{feature_name}.nc"

    if out_file.exists() and not overwrite:
        print(f"Loading cached feature: {out_file}")
        return _load_dataarray(out_file)

    # Load inputs if paths were supplied for data and climatology
    if isinstance(data, (str, Path)):
        data = _load_dataarray(data)

    if isinstance(climatology, (str, Path)):
        climatology = _load_climatology(climatology)

    if "std" not in climatology:
            raise ValueError("Climatology must contain a 'std' variable.")

    anomaly = compute_anomaly(data, climatology)

    std = _fix_region_dtype(climatology)["std"]

    # Zero or invalid standard deviations cannot be used for scaling.
    std = std.where(np.isfinite(std) & (std > 0))

    standardized = anomaly / std
    standardized.name = feature_name
    standardized.attrs["description"] = (
        "Standardised anomaly relative to the calendar-dekad climatology."
    )
    standardized.attrs["logtransform"] = int(climatology.attrs.get("logtransform", 0))


    print(f"Saving standardised feature to: {out_file}")
    standardized.to_netcdf(out_file)

    return standardized


def assemble_feature_dataset(feature_dir):

    """
    Load the 9 standardized feature files from `feature_dir`, merge them into one
    xr.Dataset and save it as <feature_dir>/feature_ds.nc (overwritten on every run).

    Each feature file must be named <feature_name>.nc, as written by standardize_anomaly().
    NaN values (the lagged first dekads of 2001) are kept; drop them when building the
    DataFrame for clustering.

    Input:
    - feature_dir: path to the folder containing the 9 feature NetCDF files.

    Returns:
    - xr.Dataset, dims (region_id, year, month, dekad), 9 data variables.
    """

    feature_dir = Path(feature_dir)
    out_file = feature_dir / "feature_ds.nc"

    # fail if any input file is missing
    missing = [n for n in FEATURE_NAMES if not (feature_dir / f"{n}.nc").exists()]
    if missing:
        raise FileNotFoundError(f"Missing feature files in {feature_dir}: {missing}")

    arrays = []
    for name in FEATURE_NAMES:
        da = _load_dataarray(feature_dir / f"{name}.nc")
        da = _fix_region_dtype(da)
        da = da.reset_coords(drop=True)                 # drop leftover scalar coords (crs, spatial_ref, ...)
        da = da.transpose("region_id", "year", "month", "dekad")
        da.name = name
        arrays.append(da)

    # join="exact" raises an error on any coordinate mismatch
    feature_ds = xr.merge(arrays, join="exact")

    feature_ds.attrs["description"] = (
        "Standardised dekadal hydro-climatic features per Naturraum, input for clustering."
    )

    # summary
    print(f"Assembled {len(feature_ds.data_vars)} features, dims: {dict(feature_ds.sizes)}")
    n_nan = {v: int(feature_ds[v].isnull().sum()) for v in feature_ds.data_vars}
    print(f"NaN count per feature: {n_nan}")

    print(f"Saving feature dataset to: {out_file}")
    feature_ds.to_netcdf(out_file)

    return feature_ds