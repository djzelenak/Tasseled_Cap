#!/usr/bin/env python

"""Taken from gdal script 'rgb2pct.py' """

try:
    from osgeo import gdal
except ImportError:
    import gdal

import sys
import os.path


class RGB:
    def __init__(self, bright, green, wet, dst_filename, fformat='GTiff', color_count=256,
                 pct_filename=None):

        self.dst_driver = gdal.GetDriverByName(fformat)

        if self.dst_driver is None:
            print('"%s" driver not registered.' % fformat)
            sys.exit(1)

        self.src_bright = gdal.Open(bright, gdal.GA_ReadOnly)
        self.src_green = gdal.Open(green, gdal.GA_ReadOnly)
        self.src_wet = gdal.Open(wet, gdal.GA_ReadOnly)

        self.ct = gdal.ColorTable()
        if pct_filename is None:
            self.err = gdal.ComputeMedianCutPCT(self.src_bright.GetRasterBand(1),
                                                self.src_green.GetRasterBand(1),
                                                self.src_wet.GetRasterBand(1),
                                                color_count, self.ct)

        else:
            self.pct_ds = gdal.Open(pct_filename)
            self.ct = self.pct_ds.GetRasterBand(1).GetRasterColorTable().Clone()

        if fformat == 'GTiff':
            self.tif_filename = dst_filename

        else:
            import tempfile

            self.tif_filedesc, self.tif_filename = tempfile.mkstemp(suffix='.tif')

        self.gtiff_driver = gdal.GetDriverByName(fformat)

        self.tif_ds = self.gtiff_driver.Create(self.tif_filename,
                                               self.src_bright.RasterXSize, self.src_bright.RasterYSize, 1)

        self.tif_ds.GetRasterBand(1).SetRasterColorTable(self.ct)

        self.tif_ds.SetProjection(self.src_bright.GetProjection())

        self.tif_ds.SetGeoTransform(self.src_bright.GetGeoTransform())

        if self.src_bright.GetGCPCount() > 0:
            self.tif_ds.SetGCPs(self.src_bright.GetGCPs(), self.src_bright.GetGCPProjection())

        self.err = gdal.DitherRGB2PCT(self.src_bright.GetRasterBand(1),
                                      self.src_green.GetRasterBand(1),
                                      self.src_wet.GetRasterBand(1),
                                      self.tif_ds.GetRasterBand(1),
                                      self.ct)

        self.tif_ds = None

        if self.tif_filename != dst_filename:
            self.tif_ds = gdal.Open(self.tif_filename)

            self.dst_driver.CreateCopy(dst_filename, self.tif_ds)

            self.tif_ds = None

            os.close(self.tif_filedesc)

            self.gtiff_driver.Delete(self.tif_filename)
