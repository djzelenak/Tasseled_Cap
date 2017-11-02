
import os
import sys
import numpy as np
import subprocess
import glob

from osgeo import gdal


def add_color_table(vrt, clr):
    """

    :param vrt:
    :param clr:
    :return:
    """
    with open(clr, "r") as color_table:
        dirname, filename = os.path.split(vrt)
        filebase, fileext = os.path.splitext(filename)

        out_vrt = f"{dirname}{os.sep}zzzz{filebase}.vrt"

        with open(vrt, "r+") as txt:
            txt_read = txt.readlines()

            key = '<VRTRasterBand dataType="Byte" band="1">'

            with open(out_vrt, "wb") as out_txt:
                for line in txt_read:
                    write_line = r"%s" % line

                    out_txt.write(write_line.encode("utf-8"))

                    if key in line:
                        color_read = color_table.readlines()

                        for ln in color_read:
                            out_txt.write(ln.encode("utf-8"))

    return out_vrt


def set_color(outdir, infile, tc_band):
    """

    :param outdir:
    :param infile:
    :param tc_band:
    :return:
    """
    base_dir = outdir
    color_dir = outdir + os.sep + "color" + os.sep + tc_band
    base_name = os.path.splitext(os.path.basename(infile))[0]

    if not os.path.exists(color_dir):
        os.makedirs(color_dir)

    clrtable = f"{tc_band}.txt"

    temp_csvfile = f"{base_dir}{os.sep}zzzz_{base_name}.csv"

    outfile = f"{color_dir}{os.sep}{base_name}.tif"

    tempoutfile = f"{base_dir}{os.sep}zzzz_{base_name}.tif"

    translate_to_copy = f"gdal_translate -of GTiff -b 1 -q {infile} {tempoutfile}"

    subprocess.call(translate_to_copy, shell=True)

    with open(temp_csvfile, "wb") as open_csv:
        open_csv.write(tempoutfile.encode("utf-8") + "\r\n".encode("utf-8"))

    temp_vrt = f"{base_dir}{os.sep}zzzz_{base_name}.vrt"

    build_vrt = f"gdalbuildvrt -q -input_file_list {temp_csvfile} {temp_vrt}"

    subprocess.call(build_vrt, shell=True)

    color_vrt = add_color_table(temp_vrt, clrtable)

    translate_to_color = f"gdal_translate -of GTiff -q {color_vrt} {outfile}"

    subprocess.call(translate_to_color, shell=True)

    # Remove temporary files
    for f in glob.glob(f"{base_dir}{os.sep}zzz*"):
        os.remove(f)

    return None


def get_data(infile):
    """

    :param infile:
    :return:
    """
    src = gdal.Open(infile, gdal.GA_ReadOnly)

    if not src is None:
        return src.GetRasterBand(1).ReadAsArray()
    else:
        print(f"Could not open file {infile}")
        sys.exit(1)


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

    return file_list


def main_work(root_dir, output_dir):
    """

    :param root_dir:
    :param output_dir:
    :return:
    """
    lookup_files = {}

    b_files = get_files(root_dir, lookfor="brightness")
    lookup_files["brightness"] = b_files

    g_files = get_files(root_dir, lookfor="greenness")
    lookup_files["greenness"] = g_files

    w_files = get_files(root_dir, lookfor="wetness")
    lookup_files["wetness"] = w_files

    for key in lookup_files.keys():
        for file in lookup_files[key]:
            print(f"Working on file {file}\n")

            set_color(outdir=output_dir, infile=file, tc_band=key)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument("-i", "--input", dest="root_dir", type=str, required=True,
                        help="The full path to the root directory containing the TC bands")

    parser.add_argument("-o", "--output", dest="output_dir", type=str, required=True,
                        help="The full path to the output root directory")

    args = parser.parse_args()

    main_work(**vars(args))