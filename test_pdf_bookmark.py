# pylint: disable=missing-docstring

import pytest

from pdf_bookmark import InvalidRomanNumeralError
from pdf_bookmark import RomanOutOfRangeError
from pdf_bookmark import roman_to_arabic
from pdf_bookmark import arabic_to_roman

from pdf_bookmark import InvalidLettersNumeralError
from pdf_bookmark import letters_to_arabic
from pdf_bookmark import arabic_to_letters


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


INVALID_LETTERS = (
    '0',
    '0342',
    'a',
    'ABC',
    'AAAAAA8',
    '9BBBB',
    '&*-+#',
    '12345',
    'jflaiffj',
    '+=_-&^%#!$%#*&)~`,.><',
)

LETTERS_PAIRS = (
    (0, ''),
    (1, 'A'),
    (2, 'B'),
    (3, 'C'),
    (8, 'H'),
    (26, 'Z'),
    (27, 'AA'),
    (52, 'ZZ'),
    (106, 'BBBBB'),
)


def test_invalid_letter():
    for letters in INVALID_LETTERS:
        with pytest.raises(InvalidLettersNumeralError):
            letters_to_arabic(letters)


def test_letters_to_arabic():
    for arabic, letters in LETTERS_PAIRS:
        assert letters_to_arabic(letters) == arabic


def test_arabic_to_letters():
    for arabic, letters in LETTERS_PAIRS:
        assert arabic_to_letters(arabic) == letters
