"""
Author: Dan Zelenak
Date: 3/8/2017
Purpose: Take a color table exported from ArcMap and convert it
into XML as a new .txt file to be used by GDAL.
"""

from argparse import ArgumentParser


def main_work(ffile, newfile):
    """

    :param ffile:
    :param newfile:
    :return:
    """
    with open(ffile, 'r') as x, open(newfile, 'w') as y:
        y.write('   <ColorInterp>Palette</ColorInterp>\n'
                '   <ColorTable>\n')
        for line in x:
            line = line.strip()  # remove any \n's
            a = line.split(' ')  # make a list of the items in line
            print(a)
            del (a[0])  # remove first item from list
            a.insert(0, '   <Entry c1=')  # insert item at beginning of list a
            a.append('/>')  # add item to the end of list a
            print(a)
            # use string formatting to rewrite items in list 'a' as a string
            # with the additional characters needed for the color table
            print(a[0], a[1], a[2], a[3], a[4])
            b = '{0}"{1}" c2="{2}" c3="{3}" c4="255"{4}\n'.format(a[0], a[1], a[2], a[3], a[4])

            y.write(b)  # write the string b to the output color table

        # write the final line to the color table
        y.write('   </ColorTable>\n')

    return None


if __name__ == "__main__":
    description = "Take a color table exported from ArcMap, convert it into XML, and write to a new .txt file\n" \
                  "which can be used by GDAL"

    parser = ArgumentParser(description=description)

    parser.add_argument("-c", "--color", dest="ffile", type=str, required=True,
                        help="The full path to the .clr table")

    parser.add_argument("-n", "--new", dest="newfile", type=str, required=True,
                        help="The full path to the output .txt file")

    args = parser.parse_args()

    main_work(**vars(args))
