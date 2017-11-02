
"""
Calculate the brightness, greenness, and wetness for an ARD scene

Author: Dan Zelenak
Date: 10/18/2017

"""

import os
import sys

import numpy as np
from osgeo import gdal

import get_scenes
import tc_bgw_coeffs


def get_raster(data, src, tc_band, out_dir, band="TAB1", ext=".tif"):
    """
    Create raster from the input numpy array
    :param data:
    :param src:
    :param tc_band:
    :return:
    """
    src_file = f"{src}{os.sep}{os.path.basename(src)[:-7]}_{band}{ext}"

    out_folder = f"{out_dir}{os.sep}{os.path.basename(src)[:-7]}"

    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    out_file = f"{out_folder}{os.sep}{os.path.basename(src)[:-7]}_{tc_band}{ext}"

    if not os.path.exists(out_file):
        ref = gdal.Open(src_file, gdal.GA_ReadOnly)

        rows = ref.RasterYSize
        cols = ref.RasterXSize

        driver = ref.GetDriver()

        out_raster = driver.Create(out_file, cols, rows, 1, gdal.GDT_Int16)

        out_band = out_raster.GetRasterBand(1)
        out_band.WriteArray(data, 0, 0)

        out_raster.SetGeoTransform(ref.GetGeoTransform())
        out_raster.SetProjection(ref.GetProjection())

        ref, out_raster = None, None

    return None


def calc(coeffs, bands, sensor):
    """

    :param coeffs: <numpy.ndarray>
    :param bands: <numpy.ndarray>
    :param sensor: <str>
    :return: <numpy.ndarray>
    """
    mask = np.zeros_like(bands["QA"], dtype=np.bool)
    mask[bands["QA"] != 1] = True

    out_array = np.zeros_like(bands["QA"], dtype=np.float)

    if sensor == "L8":
        out_array[mask] = coeffs["1"] * bands["B2"][mask] + coeffs["2"] * bands["B3"][mask] + \
                          coeffs["3"] * bands["B4"][mask] + coeffs["4"] * bands["B5"][mask] + \
                          coeffs["5"] * bands["B6"][mask] + coeffs["6"] * bands["B7"][mask]

        return out_array

    else:
        out_array[mask] = coeffs["1"] * bands["B1"][mask] + coeffs["2"] * bands["B2"][mask] + \
                          coeffs["3"] * bands["B3"][mask] + coeffs["4"] * bands["B4"][mask] + \
                          coeffs["5"] * bands["B5"][mask] + coeffs["6"] * bands["B7"][mask]

        return out_array.astype(dtype=np.int)


def get_data(scene, sensor, ext=".tif"):
    """
    Return dictionary of numpy arrays for each band
    :param scene: <str>
    :param sensor: <str>
    :param ext: <str>
    :return: <dict>
    """
    band_data = {}

    if sensor == "L8":
        band_list = ["TAB2", "TAB3", "TAB4", "TAB5", "TAB6", "TAB7", "PIXELQA"]
    else:
        band_list = ["TAB1", "TAB2", "TAB3", "TAB4", "TAB5", "TAB7", "PIXELQA"]

    for band in band_list:
        infile = f"{scene}{os.sep}{os.path.basename(scene)[:-7]}_{band}{ext}"

        src = gdal.Open(infile, gdal.GA_ReadOnly)

        src_data = src.GetRasterBand(1).ReadAsArray()

        band_data[band[-2:]] = src_data.astype(np.float32)

    return band_data


def get_coeffs(sensor):
    """

    :param scene:
    :return:
    """
    B = tc_bgw_coeffs.coeffs["brightness"][sensor]
    G = tc_bgw_coeffs.coeffs["greenness"][sensor]
    W = tc_bgw_coeffs.coeffs["wetness"][sensor]

    return {"brightness": B, "greenness": G, "wetness": W}


def get_sensor(scene):
    """

    :param scene:
    :return:
    """
    basename = os.path.basename(scene)

    return basename[0] + basename[3]


def calculate_tc(scene, out_dir):
    """

    :param scene: <str>
    :param out_dir: <str>
    :return:
    """
    sensor = get_sensor(scene=scene)

    coeffs = get_coeffs(sensor=sensor)

    print(scene, sensor)
    bands = get_data(scene=scene, sensor=sensor)

    for key in coeffs.keys():
        temp_data = calc(coeffs=coeffs[key], bands=bands, sensor=sensor)
        get_raster(data=temp_data, src=scene, out_dir=out_dir, tc_band=key)

    return None


def main_work(output_dir, ard_dir=None, txt_file=None):
    """

    :param ard_dir: <str>
    :param output_dir: <str>
    :return:
    """
    if txt_file is None and ard_dir is not None:
        file_list = get_scenes.get_files(directory=ard_dir)

        # get_scenes.get_files returns files within tarfile, only want the path to the tarfile for now
        for ind, f in enumerate(file_list):
            file_list[ind] = os.path.split(f)[0]

    elif ard_dir is None and txt_file is not None:
        with open(txt_file, "r") as input_file:
            file_list = [line[:-1] for line in input_file if ".tar" in line]

    else:
        print("Either an input directory (-i) or a file list (-f) must be specified")
        sys.exit(1)

    for f in file_list:
        calculate_tc(f, output_dir)

    return None


if __name__ == "__main__":
    from argparse import ArgumentParser

    description="Calculate the brightness, greenness, and wetness for an ARD scene"

    parser = ArgumentParser(description=description)

    parser.add_argument("-i", "--input", dest="ard_dir", type=str, required=False, default=None,
                        help="The full path to the directory containing stacked ARD TA products")
    parser.add_argument("-o", "--output", dest="output_dir", type=str, required=True,
                        help="The full path to the output directory")
    parser.add_argument("-f", "--file_list", dest="txt_file", type=str, required=False, default=None,
                        help="The full path to the .txt file containing the input file list")

    args = parser.parse_args()

    main_work(**vars(args))