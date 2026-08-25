

from importfuncs import import_hyras

pr = import_hyras(
    variable="pr",
    start_year=2014,
    end_year=2019,
    bbox=study_box,
    bboxCRS = "EPSG:3035"
)

