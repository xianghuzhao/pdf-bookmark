#!/usr/bin/env python

'''
The setup file for pdf-bookmark package
'''

from distutils.core import setup
import os
import re
import setuptools   # pylint: disable=unused-import

HERE = os.path.abspath(os.path.dirname(__file__))


def find_version():
    '''Find version'''
    with open(os.path.join(HERE, 'pdf_bookmark.py')) as file_py:
        content = file_py.read()

    version_match = re.search(
        r"^VERSION\s*=\s*['\"]([^'\"]*)['\"]", content, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def find_long_description():
    '''Find long description'''
    with open(os.path.join(HERE, 'README.md')) as file_ld:
        return file_ld.read()


setup(
    name='pdf-bookmark',
    version=find_version(),
    description='PDF Bookmark Import and Export',
    long_description=find_long_description(),
    long_description_content_type='text/markdown',
    author='Xianghu Zhao',
    author_email='xianghuzhao@gmail.com',
    url='https://github.com/xianghuzhao/pdf-bookmark',
    license='MIT',

    py_modules=['pdf_bookmark'],
    tests_require=['pytest'],
    entry_points={'console_scripts': ['pdf-bookmark = pdf_bookmark:main']},
)
