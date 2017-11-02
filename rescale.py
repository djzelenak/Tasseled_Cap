
import os
import sys
import numpy as np
from argparse import ArgumentParser
import subprocess
from osgeo import gdal


def make_raster(infile, outdir, array, tc_band):
    """

    :param infile:
    :param outdir:
    :param array:
    :param tc_band:
    :return:
    """
    basename = os.path.basename(infile)

    subdir = f"{outdir}{os.sep}{tc_band}"

    if not os.path.exists(subdir):
        os.makedirs(subdir)

    outfile = f"{subdir}{os.sep}{basename}"

    src = gdal.Open(infile, gdal.GA_ReadOnly)

    if src is None:
        print(f"Could not open {infile}")
        sys.exit(1)

    rows = src.RasterYSize
    cols = src.RasterXSize

    driver = src.GetDriver()

    out_raster = driver.Create(outfile, cols, rows, 1, gdal.GDT_Byte)

    if out_raster is None:
        print(f"Could not create raster {outfile}")
        sys.exit(1)

    out_band = out_raster.GetRasterBand(1)

    out_band.WriteArray(array)
    out_band.SetNoDataValue(0)

    out_raster.SetProjection(src.GetProjection())
    out_raster.SetGeoTransform(src.GetGeoTransform())

    out_band = None
    out_raster = None

    get_stats = f"gdalinfo -stats {outfile}"
    subprocess.call(get_stats, shell=True)

    return None


def rescale_array(array, qa, out_min=1.0, out_max=255.0):
    """

    :param array:
    :param qa:
    :param out_min:
    :param out_max:
    :return:
    """
    out_data = np.zeros_like(array, dtype=np.int32)

    out_data[qa] = (array[qa] - np.min(array[qa])) * (out_max - out_min) / (np.max(array[qa]) - np.min(array[qa]))

    return out_data


def clip_array(array, qa, limits):
    """

    :param array:
    :param limits:
    :return:
    """

    clipped = np.zeros_like(array)

    np.clip(a=array, a_min=limits[0], a_max=limits[1], out=clipped)

    return clipped


def get_percentiles(array, qa, lower_percentile=12, upper_percentile=88):
    """

    :param array:
    :param qa:
    :param lower_percentile:
    :param upper_percentile:
    :return:
    """
    return [np.percentile(array[qa], lower_percentile), np.percentile(array[qa], upper_percentile)]


def get_data(infile):
    """

    :param infile:
    :return:
    """
    src = gdal.Open(infile, gdal.GA_ReadOnly)

    if not src is None:
        array = src.GetRasterBand(1).ReadAsArray()
        return array.astype(np.int32)
    else:
        print(f"Could not open file {infile}")
        sys.exit(1)


def get_masks(tarfile):
    """

    :param tarfile:
    :return:
    """
    basename = os.path.basename(tarfile)[:-7]

    sensor = basename[0] + basename[3]

    qafile = f"{tarfile}{os.sep}{basename}_PIXELQA.tif"

    src = gdal.Open(qafile, gdal.GA_ReadOnly)

    if src is None:
        print(f"Could not open PIXELQA for {qafile}")

        sys.exit(1)

    src_data = src.GetRasterBand(1).ReadAsArray()

    mask_clear = np.zeros_like(src_data, dtype=np.bool)

    mask_fill = np.copy(mask_clear)

    if sensor == "L8":
        # PIXELQA 322, 324 are clear land/water obs. with low confidence cloud and low confidence cirrus
        mask_clear[(src_data == 322) | (src_data == 324)] = True

    else:
        # PIXELQA 66, 68 are clear land/water obs. with low confidence cloud
        mask_clear[(src_data == 66) | (src_data == 68)] = True

    mask_fill[src_data != 1] = True

    return mask_clear, mask_fill


def get_tarlist(tarfiles):
    """

    :param tarfiles:
    :return:
    """
    with open(tarfiles, "r") as tars:
        tarlist = [line[:-1] for line in tars if ".tar" in line]

    if len(tarlist) == 0:
        print(f"Could not open the .txt file {tarfiles} containing the file list")

        sys.exit(1)

    return sorted(tarlist)


def get_files(in_dir, lookfor):
    """

    :param in_dir: <str>
    :param lookfor: <str>
    :return file_list: <str[]>
    """
    file_list = []
    for root, folders, files in os.walk(in_dir):
        for file in files:
            if lookfor in file and file[-4:] == ".tif":
                file_list.append(os.path.join(root, file))

    if len(file_list) == 0:
        print(f"Could not find any files in {in_dir}")
        sys.exit(1)

    return sorted(file_list)


def main_work(tc_dir, file_list, output_dir):
    """

    :param tc_dir:
    :param output_dir:
    :param file_list:
    :return:
    """
    lookup_files = {}

    b_files = get_files(tc_dir, lookfor="brightness")
    lookup_files["brightness"] = b_files

    g_files = get_files(tc_dir, lookfor="greenness")
    lookup_files["greenness"] = g_files

    w_files = get_files(tc_dir, lookfor="wetness")
    lookup_files["wetness"] = w_files

    tarlist = get_tarlist(file_list)

    for key in lookup_files.keys():
        for ind, file in enumerate(lookup_files[key]):
            test_date_file = os.path.splitext(os.path.basename(file))[0][15:23]

            test_date_qa = os.path.splitext(os.path.basename(tarlist[ind]))[0][15:23]

            if not test_date_file == test_date_qa:
                print("There is an inconsistency between the file lists")
                sys.exit(1)

            print(f"Working on file {file}\n")

            qa_clear, qa_fill = get_masks(tarlist[ind])

            array = get_data(infile=file)

            if not np.any(qa_clear is True):
                print(f"PIXELQA has no clear pixels in scene {file}, "
                      f"using the QA_Fill mask instead to retrieve percentiles")

                limits = get_percentiles(array=array, qa=qa_fill)

            else:
                limits = get_percentiles(array=array, qa=qa_clear)

            clipped_array = clip_array(array=array, qa=qa_fill, limits=limits)

            rescaled_data = rescale_array(array=clipped_array, qa=qa_fill)

            # Use this if rescaling without the percent clip
            # rescaled_data = rescale_array(array=array, qa=qa_fill)

            make_raster(file, output_dir, rescaled_data, key)

    return None


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-tc", "--tasseledcap", dest="tc_dir", type=str, required=True,
                        help="The full path to the root directory containing the TC bands")

    parser.add_argument("-f", dest="file_list", type=str, required=True,
                        help="The full path to the txt file generated by get_scenes.py")

    parser.add_argument("-o", "--output", dest="output_dir", type=str, required=True,
                        help="The full path to the output root directory")

    args = parser.parse_args()

    main_work(**vars(args))
