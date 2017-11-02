# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 10:20:45 2017

@author: dzelenak
"""

import os
from shutil import copyfile
from argparse import ArgumentParser


def main_work(filelist, output_dir):
    """
    """
    with open(filelist, "r") as openlist:
        flist = [line[:-1] for line in openlist if ".tar" in line]
        
    for file in flist:
        basename = os.path.basename(file)[:-7]
        
        browse_name = basename + ".jpg"
        
        root = os.path.split(file)[0][8:]
            
        browse_file = os.path.join(root, browse_name)
        
        out_file = output_dir + os.sep + browse_name
        
        copyfile(src=browse_file, dst=out_file)
        
        if os.path.exists(out_file):
            print(f"Copied file {browse_file} to {output_dir}")
            
        else:
            print(f"Could not move file {browse_file} to {output_dir}")

if __name__=="__main__":
    parser = ArgumentParser()
    
    parser.add_argument("-i", dest="filelist", required=True, type=str,
                        help="The full path to the scene list text file")
    
    parser.add_argument("-o", dest="output_dir", required=True, type=str,
                        help="The full path to the output directory")
    
    args = parser.parse_args()
    
    main_work(**vars(args))