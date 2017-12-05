# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 10:46:52 2017
Grab filtered scenes, sort them based on acquisition dates, and save as new sequentially numbered files
@author: dzelenak
"""

import glob
import os
import sys
from argparse import ArgumentParser
from shutil import copyfile


def read_list(txtfile):
    """

    :param txtfile:
    :return:
    """
    with open(txtfile, "r") as txt:
        flist = [line[:-1] for line in txt if ".tar" in line]

    if len(flist) == 0:
        print(f"Could not read any lines from the files {txtfile}")

        sys.exit(1)

    return flist


def do_work(outdir, indir, filelist=None):
    """

    :param outdir:
    :param filelist:
    :param indir:
    :return:
    """

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    main_list = glob.glob(indir + os.sep + "*.tif")

    if len(main_list) == 0:
        print("Could not locate files in ", indir)
        sys.exit(1)

    if not filelist is None:
        filtered_list = read_list(filelist)

        filtered_tc = []

        for item in main_list:
            for file in filtered_list:
                basename = os.path.basename(file)[:-7]

                if basename in item:
                    filtered_tc.append(item)

        if len(filtered_tc) == 0:
            print("No matching files were found between the filtered tc and main tc lists")

            sys.exit(1)

    else:
        filtered_tc = main_list

    # Pull the dates from the filenames as integers
    dates = [int(os.path.basename(file)[15:23]) for file in filtered_tc]

    # Create list of sorted dates
    dates_sorted = sorted(dates)

    for ind, d in enumerate(dates_sorted):
        # Convert integers back to strings
        dates_sorted[ind] = str(d)

    dates_lookup = []

    for date in dates_sorted:
        for file in filtered_tc:
            fname = os.path.basename(file)

            # Find the file that matches with the date
            if fname[15:23] == date:
                dates_lookup.append(file)

    new_files = []

    for ind, file in enumerate(dates_lookup):
        new_files.append(f"{outdir}{os.sep}{str(ind + 1)}.tif")

    out_txt = outdir + os.sep + "scene_to_chrono.txt"

    with open(out_txt, "w") as txt:
        for old, new in zip(dates_lookup, new_files):
            # Copy to the new file
            copyfile(old, new)
            # Record which file corresponds to which sequential number
            txt.write(os.path.splitext(os.path.basename(old))[0] + " ---- " +
                      os.path.splitext(os.path.basename(new))[0] + "\n")


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-d", dest="indir", required=True, type=str,
                        help="Full path to the directory containing Tasseled Cap composites")

    parser.add_argument("-f", dest="filelist", required=False, type=str,
                        help="The full path to the .txt file listing the filtered scenes")

    parser.add_argument("-o", dest="outdir", required=True, type=str,
                        help="Full path to the output directory that will contain the renamed jpgs")

    args = parser.parse_args()

    do_work(**vars(args))
