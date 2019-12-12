#!/usr/bin/env python

'''
setup file for pdf-bookmark package
'''

from distutils.core import setup
import os
import setuptools

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, 'VERSION')) as version_file:
    VERSION = version_file.read().strip()

with open(os.path.join(HERE, 'README.rst')) as f:
    LONG_DESCRIPTION = f.read()

setup(name='pdf-bookmark',
      version=VERSION,
      description='PDF Bookmark Import and Export',
      long_description=LONG_DESCRIPTION,
      author='Xianghu Zhao',
      author_email='xianghuzhao@gmail.com',
      url='https://github.com/xianghuzhao/pdf-bookmark',
      license='MIT',

      py_modules=['pdf_bookmark'],
      tests_require=['pytest'],
      entry_points={'console_scripts': ['pdf-bookmark = pdf_bookmark:main']},
      )
