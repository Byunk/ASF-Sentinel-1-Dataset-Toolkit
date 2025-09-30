from pathlib import Path
from osgeo import gdal


def get_common_overlap(files: list[str | Path]) -> list[float]:
    """Get the common overlap of  a list of GeoTIFF files

    Args:
        files: a list of GeoTIFF files

    Returns:
        [ulx, uly, lrx, lry], the upper-left x, upper-left y, lower-right x, and lower-right y
        corner coordinates of the common overlap
    """

    corners = [gdal.Info(str(dem), format="json")["cornerCoordinates"] for dem in files]

    ulx = max(corner["upperLeft"][0] for corner in corners)
    uly = min(corner["upperLeft"][1] for corner in corners)
    lrx = min(corner["lowerRight"][0] for corner in corners)
    lry = max(corner["lowerRight"][1] for corner in corners)
    return [ulx, uly, lrx, lry]


def clip_hyp3_products_to_common_overlap(
    data_dir: str | Path, overlap: list[float]
) -> None:
    """Clip all GeoTIFF files to their common overlap

    Args:
        data_dir:
            directory containing the GeoTIFF files to clip
        overlap:
            a list of the upper-left x, upper-left y, lower-right-x, and lower-tight y
            corner coordinates of the common overlap
    Returns: None
    """
    files_for_mintpy = [
        "_water_mask.tif",
        "_corr.tif",
        "_unw_phase.tif",
        "_dem.tif",
        "_lv_theta.tif",
        "_lv_phi.tif",
    ]

    for extension in files_for_mintpy:
        for file in data_dir.rglob(f"*{extension}"):
            dst_file = file.parent / f"{file.stem}_clipped{file.suffix}"
            gdal.Translate(destName=str(dst_file), srcDS=str(file), projWin=overlap)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default="data")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    files = data_dir.glob("*/*_dem.tif")
    overlap = get_common_overlap(files)
    clip_hyp3_products_to_common_overlap(data_dir, overlap)
