#!/usr/bin/env python

# pylint: disable=invalid-name

'''
Import and export PDF bookmark
'''

import sys
#import subprocess
import argparse

#subprocess.check_call(['gs', '-sDEVICE=pdfwrite', '-q', '-dBATCH', '-dNOPAUSE', '-sOutputFile=output.pdf', '-dPDFSETTINGS=/prepress', 'index.info', '-f', sys.argv[1]])


def main():
    '''
    The main process
    '''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', metavar='PDF', nargs='+',
                        help='an input PDF to merge')

    args = parser.parse_args()

    return 0


if __name__ == '__main__':
    sys.exit(main())
