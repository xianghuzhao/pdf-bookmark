# pylint: disable=missing-docstring

import pytest

from pdf_bookmark import InvalidRomanNumeralError
from pdf_bookmark import RomanOutOfRangeError
from pdf_bookmark import roman_to_arabic
from pdf_bookmark import arabic_to_roman


INVALID_ROMAN = (
    '',
    'ii',
    'IIIII',
    'ID',
    'XM',
    '12345',
    'jflaiffj',
    '+=_-&^%#!$%#*&)~`,.><',
)

INVALID_ROMAN_VALUE = (
    -100000,
    -1,
    5000,
    5001,
    5002,
    10000,
)

ROMAN_PAIRS = (
    (0, 'N'),
    (1, 'I'),
    (2, 'II'),
    (3, 'III'),
    (4, 'IV'),
    (5, 'V'),
    (9, 'IX'),
    (12, 'XII'),
    (16, 'XVI'),
    (29, 'XXIX'),
    (44, 'XLIV'),
    (45, 'XLV'),
    (68, 'LXVIII'),
    (83, 'LXXXIII'),
    (97, 'XCVII'),
    (99, 'XCIX'),
    (400, 'CD'),
    (500, 'D'),
    (501, 'DI'),
    (649, 'DCXLIX'),
    (798, 'DCCXCVIII'),
    (891, 'DCCCXCI'),
    (1000, 'M'),
    (1004, 'MIV'),
    (1006, 'MVI'),
    (1023, 'MXXIII'),
    (2014, 'MMXIV'),
    (3999, 'MMMCMXCIX'),
    (4999, 'MMMMCMXCIX'),
)


def test_invalid_roman():
    for roman in INVALID_ROMAN:
        with pytest.raises(InvalidRomanNumeralError):
            roman_to_arabic(roman)


def test_roman_to_arabic():
    for arabic, roman in ROMAN_PAIRS:
        assert roman_to_arabic(roman) == arabic


def test_out_of_range_roman():
    for arabic in INVALID_ROMAN_VALUE:
        with pytest.raises(RomanOutOfRangeError):
            arabic_to_roman(arabic)


def test_arabic_to_roman():
    for arabic, roman in ROMAN_PAIRS:
        assert arabic_to_roman(arabic) == roman
