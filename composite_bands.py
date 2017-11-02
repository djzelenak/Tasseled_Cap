"""Create multi-band raster from brightness, greenness, and wetness components"""

import os
import sys
from rgb2pct import RGB
from argparse import ArgumentParser


def make_composite(out_dir, fname, bands):
    """

    :param out_dir
    :param fname:
    :param bands:
    :return:
    """
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_file = out_dir + os.sep + fname + "_tc.tif"

    RGB(bright=bands[0], green=bands[1], wet=bands[2], dst_filename=out_file)

    return None


def check_len(b, g, w):
    """

    :param b:
    :param g:
    :param w:
    :return:
    """
    if len(b) != len(g) or len(b) != len(w):
        print("There is an inconsistent number of components, please check the inputs")
        sys.exit(1)

    return None


def get_files(in_dir, lookfor):
    """

    :param in_dir:
    :param lookfor:
    :return:
    """
    flist = []

    for root, dirs, files in os.walk(in_dir):
        for file in files:
            if lookfor in file and file[-3:] == "tif":
                flist.append(os.path.join(root, file))

    return flist


def main_work(input_dir, output_dir):
    """

    :param input_dir:
    :param output_dir:
    :return:
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    brights = get_files(input_dir, lookfor="brightness")
    greens = get_files(input_dir, lookfor="greenness")
    wets = get_files(input_dir, lookfor="wetness")

    check_len(brights, greens, wets)

    components = {}

    for b, g, w in zip(brights, greens, wets):
        name = os.path.basename(b)[:40]
        print(name)
        print(b, '\n', g, '\n', w, '\n')
        components[name] = (b, g, w)

    for key in components.keys():
        make_composite(output_dir, key, components[key])

    return None


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-i", "--input", dest="input_dir", type=str, required=True,
                        help="The full path to the root directory containing tasseled cap band subfolders")

    parser.add_argument("-o", "--output", dest="output_dir", type=str, required=True,
                        help="The full path to the output directory")

    args = parser.parse_args()

    main_work(**vars(args))
