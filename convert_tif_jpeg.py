# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 13:29:34 2017
Use image magick to convert .tif to .jpeg
@author: dzelenak
"""

import glob
import os
import subprocess
import sys
from argparse import ArgumentParser


def do_work(indir, outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    tifs = glob.glob(indir + os.sep + "*.tif")

    if len(tifs) == 0:
        print("Could not locate files in ", indir)
        sys.exit(1)

    for tif in tifs:
        outfile = os.path.splitext(os.path.basename(tif))[0] + ".jpg"

        outfile = outdir + os.sep + outfile

        print(tif, '\n', outfile)

        magick = "magick.exe " + tif + " " + outfile

        subprocess.call(magick, shell=True)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-i", dest="indir", required=True, type=str,
                        help="Full path to the directory containing browse imagery")

    parser.add_argument("-o", dest="outdir", required=True, type=str,
                        help="Full path to the output directory that will contain the renamed jpgs")

    args = parser.parse_args()

    do_work(**vars(args))
