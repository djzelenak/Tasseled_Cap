
"""Calculate the percent of clear land and water pixels within a scene"""

import os
import sys
from argparse import ArgumentParser
import numpy as np

from osgeo import gdal


def write_to_txt(scenes, out_dir):
    """

    :param scenes:
    :param out_dir:
    :return:
    """
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_txt = f"{out_dir}{os.sep}cloud_filtered_scenes.txt"

    with open(out_txt, "w") as txt:
        for scene in scenes:
            txt.write(scene + "\n")

    return None


def get_cloud_cover(pixelqa, vals):
    """

    :param pixelqa:
    :param vals:
    :return:
    """
    counting_mask = np.zeros_like(pixelqa, dtype=np.bool)

    for v in vals:
        counting_mask[pixelqa == v] = True

    total_clear = np.sum(counting_mask)

    total = np.sum(np.ones_like(pixelqa))

    # Return the percent of scene covered by clouds
    return 100 - int(total_clear / total * 100)


def get_sensor(in_tar):
    """

    :param in_tar:
    :return:
    """
    return os.path.basename(in_tar)[0] + os.path.basename(in_tar)[3]


def get_pixelqa(in_tar):
    """

    :param in_tar:
    :return:
    """
    basename = os.path.basename(in_tar)[:-7]

    arch_qa = f"{in_tar}{os.sep}{basename}_PIXELQA.tif"

    src = gdal.Open(arch_qa, gdal.GA_ReadOnly)

    if src is None:
        print("Could not open PIXELQA file {arch_qa}")

        sys.exit(1)

    return src.GetRasterBand(1).ReadAsArray()


def main_work(file_list, outdir, cloud_threshold=10):
    """

    :param file_list:
    :param outdir:
    :param cloud_threshold:
    :return:
    """
    with open(file_list, "r") as tar_list:
        files = [line[:-1] for line in tar_list if ".tar" in line]

    if len(files) == 0:
        print(f"Could not read any .tar files from the given list {file_list}")

        sys.exit(1)

    filtered = []

    for file in files:
        print("Checking file {file}\n")

        pixelqa = get_pixelqa(file)

        sensor = get_sensor(file)

        if sensor == "L8":
            pqa_vals = [322, 324]

        else:
            pqa_vals = [66, 68]

        cloud_cover = get_cloud_cover(pixelqa, pqa_vals)

        if cloud_cover <= cloud_threshold:
            filtered.append(file)

    write_to_txt(filtered, outdir)

    return None


if __name__=="__main__":
    description = "This script will generate a list of files that pass a cloud cover filter test.  A pre-generated " \
                  "list of tar archives for the tile must exist - use the get_scenes.py script to generate this."

    parser = ArgumentParser(description=description)

    parser.add_argument("-f", dest="file_list", type=str, required=True,
                        help="The full path to the list of pre-filtered scenes, a .txt file")

    parser.add_argument("-o", dest="outdir", type=str, required=True,
                        help="The full path to the output directory where the cloud-filtered scene list will be saved")

    parser.add_argument("-cc", dest="cloud_threshold", type=int, required=False, metavar="0 - 100",
                        help="The percent of maximum cloud cover a scene must have to be allowed through the filter")

    args = parser.parse_args()

    main_work(**vars(args))

