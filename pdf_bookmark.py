#!/usr/bin/env python

# pylint: disable=invalid-name

'''
Import and export PDF bookmark
'''

import sys
import subprocess
import re
import argparse


MAP_NUM_STYLE = {
    'DecimalArabicNumerals': 'Arabic',
    'UppercaseRomanNumerals': 'Roman',
    'LowercaseRomanNumerals': 'Roman',
    'UppercaseLetters': 'Letters',
    'LowercaseLetters': 'Letters',
}


ROMAN_NUMERAL_PAIR = (
    ('M', 1000),
    ('CM', 900),
    ('D', 500),
    ('CD', 400),
    ('C', 100),
    ('XC', 90),
    ('L', 50),
    ('XL', 40),
    ('X', 10),
    ('IX', 9),
    ('V', 5),
    ('IV', 4),
    ('I', 1),
)

ROMAN_NUMERAL_MAP = {pair[0]: pair[1] for pair in ROMAN_NUMERAL_PAIR}


ROMAN_NUMERAL_PATTERN = re.compile(
    '^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'
)


class InvalidNumeralError(Exception):
    '''Invalid numeral expression'''


class InvalidRomanNumeralError(InvalidNumeralError):
    '''Invalid roman numeral expression'''


class RomanOutOfRangeError(Exception):
    '''The roman number is out of range'''


class InvalidLettersNumeralError(InvalidNumeralError):
    '''Invalid letters numeral expression'''


class LettersOutOfRangeError(Exception):
    '''The letters number is out of range'''


def roman_to_arabic(roman):
    '''
    Convert roman to arabic
    '''
    if not roman:
        raise InvalidRomanNumeralError('No input found')

    if roman == 'N':
        return 0

    if not ROMAN_NUMERAL_PATTERN.match(roman):
        raise InvalidRomanNumeralError(
            'Invalid Roman numeral: {}'.format(roman))

    arabic = 0
    for i, n in enumerate(roman):
        if i == len(roman)-1 or ROMAN_NUMERAL_MAP[roman[i]] >= ROMAN_NUMERAL_MAP[roman[i+1]]:
            arabic += ROMAN_NUMERAL_MAP[n]
        else:
            arabic -= ROMAN_NUMERAL_MAP[n]

    return arabic


def arabic_to_roman(arabic):
    '''
    Convert arabic to roman
    '''
    if arabic < 0 or arabic > 4999:
        raise RomanOutOfRangeError('Roman numeral must in [0, 5000)')

    if arabic == 0:
        return 'N'

    roman = ''

    remain = arabic
    for digit, unit in ROMAN_NUMERAL_PAIR:
        digit_num = remain // unit
        roman += digit*digit_num
        remain -= unit*digit_num

    return roman


def letters_to_arabic(letters):
    '''
    Convert letters to arabic
    '''
    if not letters:
        return 0

    letter = letters[0]
    if ord(letter) < ord('A') or ord(letter) > ord('Z'):
        raise InvalidLettersNumeralError('Must be capital letter')

    for digit in letters[1:]:
        if digit != letter:
            raise InvalidLettersNumeralError('Letters are not identical')

    return len(letters)*26 - 25 + ord(letter) - ord('A')


def arabic_to_letters(arabic):
    '''
    Convert arabic to letters
    '''
    if arabic < 0:
        raise LettersOutOfRangeError('Letters numeral must >= 0')

    if arabic == 0:
        return ''

    return chr(((arabic-1) % 26) + ord('A')) * ((arabic+25) // 26)


def call(cmd, encoding=None):
    '''
    Run command
    '''
    if encoding is None:
        encoding = 'utf-8'

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    status = p.wait()

    if status != 0:
        raise Exception(
            'Invoke command {} failed with exit code {}:\n {}'.format(
                cmd, status, err.decode(encoding)))

    if encoding:
        out = out.decode(encoding)
    return out


def pdftk_to_bookmark(data):
    '''
    Convert pdftk output to bookmark
    '''
    bookmark = []

    for line in data.splitlines():
        try:
            key, value = line.split(': ', 1)
        except ValueError:  # e.g. line == 'InfoBegin'
            continue
        if key.startswith('Bookmark'):
            bookmark.append(value)

    return bookmark


def main():
    '''
    The main process
    '''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', metavar='PDF', help='an input PDF')
    parser.add_argument(
        '--expand-level', help='the max level to be expanded')

    args = parser.parse_args()

    pdftk_data = call(['pdftk', args.pdf, 'dump_data'], 'ascii')

    bookmark_data = pdftk_to_bookmark(pdftk_data)
    print(bookmark_data)

    return 0


if __name__ == '__main__':
    sys.exit(main())
