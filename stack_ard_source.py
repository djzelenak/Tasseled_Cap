"""
Stack files directly from the ARD .tar archives
Built from Kelcy Smith's espa_to_envi_c01b.py script.
Works for TA or SR.

Date: 11/3/2017
"""

import os
import subprocess
import multiprocessing as mp
import tarfile
import shutil
import logging
import sys
import argparse

from osgeo import gdal


# TODO add option to select TA, SR, BT, QA

LOGGER = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
handler.setFormatter(formatter)
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)


def create_tiles(inpath, outpath, worker_num, work_dir, product):
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    file_q = mp.Queue()
    message_q = mp.Queue()

    file_enqueue(inpath, file_q, worker_num, product)
    work = work_paths(worker_num, work_dir)

    message = mp.Process(target=progress, args=(message_q, worker_num))
    message.start()
    for i in range(worker_num - 1):
        print(work[i])
        p_args = (file_q, message_q, outpath, work[i], product)
        print(p_args)
        mp.Process(target=process_tile, args=p_args).start()

    message.join()


def unpackage(file, work_path):
    with tarfile.open(file) as f:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(f, path=work_path)


def translate(pathing):
    subprocess.call('gdal_translate -of GTiff {} {}'
                    .format(pathing['TRAN']['IN'], pathing['TRAN']['OUT']), shell=True)


def vrt(pathing):
    subprocess.call('gdalbuildvrt -separate {} {}'
                    .format(pathing['VRT']['OUT'], pathing['VRT']['IN']), shell=True)


def build_paths(out_path, tiff_base, work_path, band_list, prod):
    base = os.path.join(out_path, tiff_base)

    if not os.path.exists(base):
        os.makedirs(base)

    phs = {'VRT': {'OUT': os.path.join(work_path, tiff_base + '.vrt'),
                   'IN': ' '.join(band_list)},
           'TRAN': {'IN': os.path.join(work_path, tiff_base + '.vrt'),
                    'OUT': os.path.join(base, tiff_base + f'_{prod}stack.tif')}}

    return phs


def build_l8_list(work_path, tiff_base, prod):
    return ['{}_{}B2.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B3.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B4.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B5.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B6.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B7.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_PIXELQA.tif'.format(os.path.join(work_path, tiff_base))]


def build_tm_list(work_path, tiff_base, prod):
    return ['{}_{}B1.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B2.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B3.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B4.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B5.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_{}B7.tif'.format(os.path.join(work_path, tiff_base), prod),
            '{}_PIXELQA.tif'.format(os.path.join(work_path, tiff_base))]


def base_name(work_path, prod):
    base = ''
    for tiff_file in os.listdir(work_path):
        if tiff_file[-9:] != f'_{prod}B2.tif':
            continue

        base = tiff_file[:-9]
        break

    return base


def clean_up(work_path):
    for f in os.listdir(work_path):
        os.remove(os.path.join(work_path, f))


def find_tile_name(file):
    ds = gdal.Open(file)

    affine = extent_to_hv(ds.GetGeoTransform())

    ds = None

    return affine


def process_tile(file_q, prog_q, out_path, work_path, prod):
    """Process a file from the queue"""
    proc = work_path[-1]
    print(proc)

    while True:
        try:
            file = file_q.get()
            print(file)
            if file == 'KILL':
                prog_q.put('Killing process %s' % proc)
                break

            # srpath, btpath = file


            prog_q.put('Process %s: Unpacking %s' % (proc, file))
            unpackage(file, work_path)


            tiff_base = base_name(work_path, prod)
            print(tiff_base)

            if tiff_base[3] == '8':
                band_list = build_l8_list(work_path, tiff_base, prod)
            else:
                band_list = build_tm_list(work_path, tiff_base, prod)

            pathing = build_paths(out_path, tiff_base, work_path, band_list, prod)

            print(pathing)

            if os.path.exists(pathing['TRAN']['OUT']):
                clean_up(work_path)
                continue

            prog_q.put('Process %s: Building VRT stack for %s' % (proc, tiff_base))
            vrt(pathing)

            prog_q.put('Process %s: Calling Translate for %s' % (proc, tiff_base))
            translate(pathing)

            clean_up(work_path)
        except Exception as e:
            prog_q.put('Process %s: Hit an exception - %s' % (proc, e))
            prog_q.put('Killing process %s' % proc)
            clean_up(work_path)
            break

    os.rmdir(work_path)


def file_enqueue(path, q, worker_num, prod):
    """Builds a queue of files to be processed"""

    for root, dirs, files in os.walk(path):
        for file in files:
            if file[-6:] == f'{prod}.tar':

                a = os.path.join(root, file)
                print(a)
                q.put(a)

    for _ in range(worker_num):
        q.put('KILL')


def work_paths(worker_num, path):
    """Makes working directories for the multi-processing"""

    out = []
    for i in range(worker_num - 1):
        new_path = os.path.join(path, 'espa_ard_working%s' % i)
        out.append(new_path)
        if not os.path.exists(new_path):
            os.makedirs(new_path)

    return out


def progress(prog_q, worker_num):
    count = 0
    while True:
        message = prog_q.get()

        LOGGER.info(message)

        if message[:4] == 'Kill':
            count += 1
        if count >= worker_num - 1:
            break


def extent_to_hv(geoaffine):
    conus_uly = 3314805
    conus_ulx = -2565585

    ul_x, _, _, ul_y, _, _ = geoaffine

    h = int((ul_x - conus_ulx) / 150000)
    v = int((conus_uly - ul_y) / 150000)

    return 'h{0}v{1}'.format(h, v)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", dest="inpath", type=str, required=True,
                        help="Full path to the tarball inputs")

    parser.add_argument("-o", "--output", dest="outpath", type=str, required=True,
                        help="Full path to the output folder")

    parser.add_argument("-p", "--product", dest="product", type=str, required=True,
                        help="The product type - TA, SR")

    parser.add_argument("-n", "--workers", dest="worker_num", type=int, required=False, default=20,
                        help="The number of consecutive processes, default is 20")

    parser.add_argument("-w", "--workingdir", dest="work_dir", required=True,
                        help="The full path to the working directory")

    args = parser.parse_args()

    create_tiles(**vars(args))
