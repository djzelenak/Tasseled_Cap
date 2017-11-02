
"""
Test a directory of stacked ARD TA imagery for the presence of a specified PIXELQA value at a given
XY coordinate.  Scenes that DO NOT equal this value are considered acceptable.  Generate a text file containing
the full path to each of the accepted ARD scenes.

Requires pre-unpacked and stacked TA imagery.  Band 7 must contain the PIXELQA.

Author: Dan Zelenak
Date: 10/18/2017

"""
import os

from geo_utils import ChipExtents
from osgeo import gdal


def get_txt(outdir, files, coords, value, hv):
    """
    Generate a .txt file containing the paths to accepted ARD scenes
    :param outdir: <str>
    :param files: <list>
    :param coords:
    :param value:
    :param hv:
    :return:
    """
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    out_file = f"{outdir}{os.sep}file_list.txt"

    with open(out_file, "w") as txt_file:
        txt_file.write(f"Checked for QA Value {value} at location {coords} in tile H{hv[0]}V{hv[1]}\n")

        for f in files:
            txt_file.write(f"{f}\n")

    return None


def get_data(image):
    """
    Open the image and its as a numpy array
    :param image: <str>
    :return: <numpy.ndarray>
    """
    src = gdal.Open(image, gdal.GA_ReadOnly)

    return src.GetRasterBand(1).ReadAsArray()


def get_files(directory, lookfor="PIXELQA", ext=".tif"):
    """
    Return list of files with full path appending /vsitar/ to open from within tarfile
    :param directory: <str>
    :param lookfor: <str>
    :param ext: <str>
    :return:
    """
    flist = []

    for root, folders, files in os.walk(directory):
        for file in files:
            if file[-6:] == "TA.tar":
                tarfile = os.path.join(root, file)

                basename = os.path.basename(tarfile)

                entity_id = basename[:-7]

                full_path = f"/vsitar/{tarfile}{os.sep}{entity_id}_{lookfor}{ext}"

                flist.append(full_path)

    return flist


def check_value(qa_file, value, rowcol):
    """
    Check the QAMap at the given coordinates for the given value
    :param qa_file: <str>
    :param value: <int>
    :param rowcol: <namedtuple ChipExtents.GeoCoordinate> rowcol.row, rowcol.col
    :return:
    """
    qa_data = get_data(qa_file)

    print(f"Checking file {os.path.basename(qa_file)}")

    if not qa_data[rowcol.row, rowcol.column] == value:
        return True

    else:
        return False


def main_work(ard_dir, output_dir, coords, qa_value, tile_hv):
    """

    :param ard_dir: <str>
    :param output_dir: <str>
    :param coords: <list>
    :param qa_value: <int>
    :param tile_hv: <list, int>
    :return:
    """
    chip_info = ChipExtents(h=tile_hv[0], v=tile_hv[1])

    geo_coord = chip_info.GeoCoordinate(x=coords[0], y=coords[1])

    row_col = chip_info.geo_to_rowcol(chip_info.PIXEL_AFFINE, geo_coord)

    # print(row_col.row, row_col.column)

    input_list = get_files(ard_dir)

    # print(input_list)

    file_list = [os.path.split(i)[0] for i in input_list if check_value(i, qa_value, row_col) is True]

    get_txt(output_dir, file_list, coords, qa_value, tile_hv)

    return None


if __name__ == "__main__":
    from argparse import ArgumentParser

    description = "Produce a filtered list of paths to ARD TA tarfiles based on the PIXELQA " \
                  "value for a user-defined XY coordinate"

    parser = ArgumentParser(description=description)

    parser.add_argument("-i", "--input", dest="ard_dir", type=str, required=True,
                        help="The full path to the directory containing ARD TA tarfiles")
    parser.add_argument("-o", "--output", dest="output_dir", type=str, required=True,
                        help="The full path to the output directory")
    parser.add_argument("-xy", "--xy", dest="coords", type=int, required=True, nargs=2, metavar=("X-coord", "Y-coord"),
                        help="The x and y coordinates used to test for target imagery")
    parser.add_argument("-hv", "--hv", dest="tile_hv", type=int, required=True, nargs=2, metavar=("HH", "VV"),
                        help="The ARD tile H and V designation")
    parser.add_argument("-qa", "--qa", dest="qa_value", type=int, required=False, default=1,
                        help="The QA value used to determine if a scene is valid")

    args = parser.parse_args()

    main_work(**vars(args))
