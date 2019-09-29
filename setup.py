#!/usr/bin/env python

from distutils.core import setup

setup(name='pdf-bookmark',
      version='1.0',
      description='PDF Bookmark Import and Export',
      author='Xianghu Zhao',
      author_email='xianghuzhao@gmail.com',
      url='https://github.com/xianghuzhao/pdf-bookmark',
      py_modules=['pdf_bookmark'],
      entry_points={'console_scripts': ['pdf-bookmark = pdf_bookmark:main']},
      )
