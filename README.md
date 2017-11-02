# Tasseled Cap

## Requirements

Python == 3.6.2*

gdal == 2.2.1*

numpy == 1.12.1*

*These versions are based on the virtual environment in which these
scripts were written.  Other versions may work, but have not been tested.

## Purpose:

Various tools to generate tasseled cap brightness, greenness, and
wetness from Landsat ARD.

## Workflow:

##### 1 get_scenes.py

Generate a text file that lists the scenes to be used from the original
ARD stack.  The scenes are filtered based on the pixel value at a
specified location.  The script checks the PIXELQA value at those
coordinates for the presence of "fill".  The script can check for the
default fill value of 1, or optionally a different PIXELQA value can be
specified.

##### 2 tasseled_cap.py

Calculate the brightness, greenness, and wetness bands from the Landsat
ARD.  Either use the filtered scene list, or the entire ARD stack.  The
outputs will be saved in subfolders named with the corresponding TC band.
  The datatype of the output rasters is Int16.

##### 3 rescale.py

Perform a percent clipping on the tasseled cap bands.  Calculate
upper and lower percentiles using only clear land and water observations.
These are determined using the scene's PIXELQA band.  The script checks
for the sensor to use the correct PIXELQA values.  The default percentile
values are:

lower_percentile = 12

upper_percentile = 88

These can be specified optionally at the command line.  After the percent
clip, the data is rescaled to 0-255 and saved as new unsigned 8-bit
integer rasters.

##### 4 add_color.py

The color tables stored in the .txt files (brightness.txt, greenness.txt,
 wetness.txt) are applied to the rescaled TC bands and saved as new
 rasters.

##### 5 composite_bands.py

Generate false color RGB composites from the rescaled TC bands.

Red = Brightness

Green = Greenness

Blue = Wetness

##### 6 get_sorted_*.py

Copy and save the colorized TC bands and TC composites as sequentially
numbered rasters.  Ordering is based on the acquisition date.

##### Optional pixelqa_scene_filter.py

This script will generate a list of scenes that have a maximum amount
of cloud cover (as a percent).  The default value is 10% but a specified
value can be passed at the command line.  Any scenes that have this value
or less cloud cover are included in the filtered list.  Cloud cover
percent is determined by counting the number of clear land and water
observations with low cloud and low cirrus confidence (from PIXELQA)
and dividing by the total number of pixels in the scene.

This list can be used to filter the final scenes in the "get_sorted"
scripts.

