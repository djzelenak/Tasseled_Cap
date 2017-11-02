# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 10:46:52 2017
Grab the filtered scenes, sort them based on acquisition dates, and save them as new sequentially numbered files
@author: dzelenak
"""

import os
import sys
import pprint
from shutil import copyfile
from argparse import ArgumentParser


def read_list(txtfile):
    """

    :param txtfile:
    :return:
    """
    with open(txtfile, "r") as txt:
        flist = [line[:-1] for line in txt if ".tar" in line]

    if len(flist) == 0:
        print(f"Could not read any lines from the file {txtfile}")

        sys.exit(1)

    return flist


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


def do_work(outdir, filelist, tc_dir):
    """

    :param outdir:
    :param filelist:
    :param tc_dir:
    :return:
    """

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    lookup_files = {}

    b_files = get_files(tc_dir, lookfor="brightness")
    lookup_files["brightness"] = b_files

    g_files = get_files(tc_dir, lookfor="greenness")
    lookup_files["greenness"] = g_files

    w_files = get_files(tc_dir, lookfor="wetness")
    lookup_files["wetness"] = w_files

    filtered_lookup = {}

    filtered_list = read_list(filelist)

    for key in lookup_files.keys():
        temp_list = []

        for ind, file in enumerate(lookup_files[key]):
            for item in filtered_list:
                basename = os.path.basename(item)[:-7]

                if basename in file:
                    temp_list.append(file)

        filtered_lookup[key] = sorted(temp_list)

        if len(filtered_lookup[key]) == 0:
            print("No matching files were found between the filtered browse and main browse lists")

            sys.exit(1)

    # Pull the dates from the filenames as integers
    dates = [int(os.path.basename(file)[15:23]) for file in filtered_lookup["brightness"]]

    # Create list of sorted dates
    dates_sorted = sorted(dates)

    for ind, d in enumerate(dates_sorted):
        # Convert integers back to strings
        dates_sorted[ind] = str(d)

    dates_lookup = {}

    for key in filtered_lookup.keys():
        temp_list = []

        for date in dates_sorted:
            for file in filtered_lookup[key]:
                fname = os.path.basename(file)

                if fname[15:23] == date:
                    temp_list.append(file)

        dates_lookup[key] = temp_list

    pprint.pprint(dates_lookup)

    new_files = {}

    for key in dates_lookup.keys():
        temp_list = []

        for ind, file in enumerate(dates_lookup[key]):
            temp_list.append(f"{outdir}{os.sep}{key}{os.sep}{str(ind + 1)}.tif")

            if not os.path.exists(f"{outdir}{os.sep}{key}"):
                os.makedirs(f"{outdir}{os.sep}{key}")

        new_files[key] = temp_list

    pprint.pprint(new_files)

    out_txt = outdir + os.sep + "tcband_to_chrono.txt"

    with open(out_txt, "w") as txt:
        for key in dates_lookup.keys():
            for old, new in zip(dates_lookup[key], new_files[key]):
                # Copy to the new file
                copyfile(old, new)
                # Record which file corresponds to which sequential number
                txt.write(os.path.splitext(os.path.basename(old))[0] + " ---- " +
                          os.path.splitext(os.path.basename(new))[0] + "\n")


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-tc", dest="tc_dir", required=True, type=str,
                        help="Full path to the root directory containing tasseled cap bands")

    parser.add_argument("-f", dest="filelist", required=True, type=str,
                        help="The full path to the .txt file listing the filtered scenes")

    parser.add_argument("-o", dest="outdir", required=True, type=str,
                        help="Full path to the output directory that will contain the renamed jpgs")

    args = parser.parse_args()

    do_work(**vars(args))
