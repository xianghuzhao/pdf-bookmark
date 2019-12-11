#!/usr/bin/env python

# pylint: disable=invalid-name

'''
Import and export PDF bookmark
'''

import os
import sys
import subprocess
import re
import argparse
import json
import tempfile
import codecs


_NUM_STYLE_MAP = {
    'DecimalArabicNumerals': 'Arabic',
    'UppercaseRomanNumerals': 'Roman',
    'LowercaseRomanNumerals': 'Roman',
    'UppercaseLetters': 'Letters',
    'LowercaseLetters': 'Letters',
}


_ROMAN_NUMERAL_PAIR = (
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

_ROMAN_NUMERAL_MAP = {pair[0]: pair[1] for pair in _ROMAN_NUMERAL_PAIR}

_ROMAN_NUMERAL_PATTERN = re.compile(
    '^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'
)


_BOOKMARK_DESCRIPTION = {
    'bookmark': {
        'prefix': 'Bookmark',
        'fields': {
            'Title': 'title',
            'Level': 'level',
            'PageNumber': 'page',
        },
        'handler': {
            'title': lambda s: _unicode_replace(s) if _UNICODE_REGEXP.search(s) else s,
            'level': int,
            'page': int,
        },
    },
    'page_label': {
        'prefix': 'PageLabel',
        'fields': {
            'NewIndex': 'new_index',
            'Start': 'num_start',
            'NumStyle': 'num_style',
        },
        'handler': {
            'new_index': int,
            'num_start': int,
            'num_style': lambda s: _NUM_STYLE_MAP.get(s, 'Arabic'),
        },
    },
}


_UNICODE_REGEXP = re.compile('&#([0-9]+);')


_CONTENT_MINIMUM_DOTS = 4


class InvalidBookmarkSyntaxError(Exception):
    '''Invalid bookmark syntax'''


class InvalidNumeralError(ValueError):
    '''Invalid numeral expression'''


class InvalidRomanNumeralError(InvalidNumeralError):
    '''Invalid roman numeral expression'''


class RomanOutOfRangeError(Exception):
    '''The roman number is out of range'''


class InvalidLettersNumeralError(InvalidNumeralError):
    '''Invalid letters numeral expression'''


class LettersOutOfRangeError(Exception):
    '''The letters number is out of range'''


def echo(s, nl=True):
    '''
    Print to stdout
    '''
    sys.stdout(s)
    if nl:
        sys.stdout('\n')
    sys.stdout.flush()


def roman_to_arabic(roman):
    '''
    Convert roman to arabic
    '''
    if not roman:
        raise InvalidRomanNumeralError('No input found')

    if roman == 'N':
        return 0

    if not _ROMAN_NUMERAL_PATTERN.match(roman):
        raise InvalidRomanNumeralError(
            'Invalid Roman numeral: {}'.format(roman))

    arabic = 0
    for i, n in enumerate(roman):
        if i == len(roman)-1 or _ROMAN_NUMERAL_MAP[roman[i]] >= _ROMAN_NUMERAL_MAP[roman[i+1]]:
            arabic += _ROMAN_NUMERAL_MAP[n]
        else:
            arabic -= _ROMAN_NUMERAL_MAP[n]

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
    for digit, unit in _ROMAN_NUMERAL_PAIR:
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


def _unicode_replace_match(match):
    return chr(int(match.group(1)))


def _unicode_replace(string):
    return _UNICODE_REGEXP.sub(_unicode_replace_match, string)


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


def import_pdftk(data, collapse_level=0):
    '''
    Convert pdftk output to bookmark
    '''
    bookmarks = {}
    bookmark_info = {}

    for t in _BOOKMARK_DESCRIPTION:
        bookmarks[t] = []
        bookmark_info[t] = {}

    for line in data.splitlines():
        try:
            key, value = line.split(': ', 1)
        except ValueError:  # e.g. line == 'InfoBegin'
            continue

        for bm_type, bm_detail in _BOOKMARK_DESCRIPTION.items():
            if not key.startswith(bm_detail['prefix']):
                continue

            k = key[len(bm_detail['prefix']):]
            if k not in bm_detail['fields']:
                continue

            k = bm_detail['fields'][k]
            if k in bm_detail['handler']:
                v = bm_detail['handler'][k](value)

            bookmark_info[bm_type][k] = v

            ready_for_save = True
            for _, field in bm_detail['fields'].items():
                if field not in bookmark_info[bm_type]:
                    ready_for_save = False
                    break
            if not ready_for_save:
                continue

            bookmark_info[bm_type]['collapse'] = collapse_level != 0 and \
                bookmark_info[bm_type]['level'] >= collapse_level

            bookmarks[bm_type].append(bookmark_info[bm_type])
            bookmark_info[bm_type] = {}

    return bookmarks


def export_bmk(bookmarks):
    '''
    Export to bookmark format
    '''
    bm_output = '!!! # Generated bmk file\n'

    page_labels = bookmarks['page_label']

    current_page_label_index = -1

    current_collapse_level = 0

    for bm in bookmarks['bookmark']:
        page_label_index = -1
        for i, pl in enumerate(page_labels):
            if bm['page'] >= pl['new_index']:
                page_label_index = i

        if page_label_index >= 0:
            if page_label_index != current_page_label_index:
                bm_output += '\n'

                for k in ['new_index', 'num_start', 'num_style']:
                    bm_output += '!!! {} = {}\n'.format(
                        k, page_labels[page_label_index][k])

                bm_output += '\n'

                current_page_label_index = page_label_index

            page = bm['page'] - \
                page_labels[page_label_index]['new_index'] + \
                page_labels[page_label_index]['num_start']

            if page_labels[page_label_index]['num_style'] == 'Roman':
                page = arabic_to_roman(page)
            elif page_labels[page_label_index]['num_style'] == 'Letters':
                page = arabic_to_letters(page)
        else:
            page = bm['page']

        # This is a XOR of (bm['collapse']) and
        # (current_collapse_level == 0 or current_collapse_level > bm['level'])
        if bm['collapse'] == (current_collapse_level == 0 or current_collapse_level > bm['level']):
            current_collapse_level = bm['level'] if bm['collapse'] else 0
            bm_output += '!!! collapse_level = {}\n'.format(
                current_collapse_level)

        bm_output += '{}{}................{}\n'.format(
            '  '*(bm['level']-1), bm['title'], page)

    return bm_output


def _parse_bookmark_command(line):
    if line[3:].lstrip().startswith('#'):
        return '', ''

    try:
        k, v = line[3:].split('=', 1)
    except ValueError:
        raise InvalidBookmarkSyntaxError('Invalid syntax: {}'.format(line))

    return k.strip(), v.strip()


def _parse_level(line, level_indent):
    space_count = 0
    for c in line:
        if c != ' ':
            break
        space_count += 1

    if space_count % level_indent != 0:
        raise InvalidBookmarkSyntaxError(
            'Level indentation error: {}'.format(line))

    return space_count // level_indent + 1, line[space_count:]


def _split_title_page(title_page):
    start_pos = title_page.find('.'*_CONTENT_MINIMUM_DOTS)
    if start_pos < 0:
        raise InvalidBookmarkSyntaxError(
            'There must be at least {} "." specified'.format(_CONTENT_MINIMUM_DOTS))

    end_pos = start_pos + _CONTENT_MINIMUM_DOTS
    for c in title_page[start_pos+_CONTENT_MINIMUM_DOTS:]:
        if c != '.':
            break
        end_pos += 1

    title = title_page[:start_pos]
    page = title_page[end_pos:]

    return title.strip(), page.strip()


def import_bmk(bookmark_data, collapse_level=0):
    '''
    Import bookmark format
    '''
    bookmarks = {}
    bookmarks['bookmark'] = []
    bookmarks['page_label'] = []

    page_config = {
        'new_index': 1,
        'num_start': 1,
        'num_style': 'Arabic',
        'collapse_level': collapse_level,
        'level_indent': 2,
    }

    page_label_saved = False

    for line in bookmark_data.splitlines():
        if not line.strip():
            continue

        if line.startswith('!!!'):
            k, v = _parse_bookmark_command(line)
            if not k:
                continue
            if k == 'new_index':
                page_label_saved = False
                page_config[k] = int(v)
                page_config['num_start'] = 1
                page_config['num_style'] = 'Arabic'
            elif k in ['num_start', 'collapse_level', 'level_indent']:
                page_config[k] = int(v)
            else:
                page_config[k] = v
            continue

        if not page_label_saved:
            bookmarks['page_label'].append({kk: vv for kk, vv in page_config.items() if kk in [
                'new_index', 'num_start', 'num_style']})
            page_label_saved = True

        level, title_page = _parse_level(line, page_config['level_indent'])

        title, page = _split_title_page(title_page)

        try:
            if page_config['num_style'] == 'Roman':
                page = roman_to_arabic(page.upper())
            elif page_config['num_style'] == 'Letters':
                page = letters_to_arabic(page.upper())
            else:
                page = int(page)
        except ValueError:
            raise InvalidBookmarkSyntaxError(
                'Page number invalid: {}'.format(page))

        page = page - page_config['num_start'] + page_config['new_index']

        collapse = page_config['collapse_level'] != 0 and level >= page_config['collapse_level']

        bookmark_info = {
            'level': level,
            'title': title,
            'page': page,
            'collapse': collapse,
        }
        bookmarks['bookmark'].append(bookmark_info)

    return bookmarks


def _pdfmark_unicode(string):
    r"""
    >>> _pdfmark_unicode('ascii text with ) paren')
    '(ascii text with \\) paren)'
    >>> _pdfmark_unicode('\u03b1\u03b2\u03b3')
    '<FEFF03B103B203B3>'
    """
    try:
        string.encode('ascii')
    except UnicodeEncodeError:
        b = codecs.BOM_UTF16_BE + string.encode('utf-16-be')
        return '<{}>'.format(''.join('{:02X}'.format(byte) for byte in b))
    else:
        # escape special characters
        for a, b in [('\\', '\\\\'), ('(', '\\('), (')', '\\)'),
                     ('\n', '\\n'), ('\t', '\\t')]:
            string = string.replace(a, b)
        return '({})'.format(string)


def _pdfmark_unicode_decode(string):
    r"""
    >>> _pdfmark_unicode_decode(_pdfmark_unicode('\u03b1\u03b2\u03b3'))
    '\u03b1\u03b2\u03b3'
    """
    if not (string.startswith('<FEFF') and string.endswith('>')):
        raise Exception

    b = bytes(int(float.fromhex(x1+x2))
              for x1, x2 in zip(string[5:-2:2], string[6:-1:2]))
    return b.decode('utf-16-be')


def export_pdfmark(bookmarks):
    '''
    Convert bookmark to pdfmark
    '''
    pdfmark = ''

    for i, bm in enumerate(bookmarks['bookmark']):
        pdfmark += '['

        count = 0
        for bmk in bookmarks['bookmark'][i+1:]:
            if bmk['level'] == bm['level']:
                break
            if bmk['level'] == bm['level'] + 1:
                count += 1
        if count:
            sign = '-' if bm.get('collapse') else ''
            pdfmark += '/Count {}{} '.format(sign, count)

        pdfmark += '/Title {} /Page {} '.format(
            _pdfmark_unicode(bm['title']), bm['page'])

        pdfmark += '/OUT pdfmark\n'

    return pdfmark


def _write_pdfmark_noop_file():
    # By default, Ghostscript will preserve pdfmarks from the sources PDFs
    fd, filename = tempfile.mkstemp(prefix='pdfmark-noop-', text=True)
    # Make `[... /OUT pdfmark` a no-op.
    os.write(fd, b"""
% store the original pdfmark
/originalpdfmark { //pdfmark } bind def

% replace pdfmark with a wrapper that ignores OUT
/pdfmark
{
  {  % begin loop

      { counttomark pop }
    stopped
      { /pdfmark errordict /unmatchedmark get exec stop }
    if

    dup type /nametype ne
      { /pdfmark errordict /typecheck get exec stop }
    if

    dup /OUT eq
      { (Skipping OUT pdfmark\n) print cleartomark exit }
    if

    originalpdfmark exit

  } loop
} def
""")
    os.close(fd)
    return filename


def _write_pdfmark_restore_file():
    fd, filename = tempfile.mkstemp(prefix='pdfmark-restore-', text=True)
    # Restore the default `[... /Out pdfmark` behaviour
    os.write(fd, b'/pdfmark { originalpdfmark } bind def\n')
    os.close(fd)
    return filename


def generate_pdf(pdfmark, pdf, output_pdf):
    '''
    Generate pdf from pdfmark and pdf file
    '''
    fd, pdfmark_file = tempfile.mkstemp(prefix='pdfmark_')
    with open(fd, 'w') as f:
        f.write(pdfmark)

    pdfmark_noop = _write_pdfmark_noop_file()
    pdfmark_restore = _write_pdfmark_restore_file()

    call(['gs', '-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite',
          '-sOutputFile={}'.format(output_pdf),
          pdfmark_noop,
          pdf,
          pdfmark_restore,
          pdfmark_file])

    os.remove(pdfmark_noop)
    os.remove(pdfmark_restore)
    os.remove(pdfmark_file)


def main():
    '''
    The main process
    '''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-f', '--format', default='bmk',
        choices=['bmk', 'none', 'pdftk', 'pdfmark', 'json'],
        help='the output format of bookmark')
    parser.add_argument(
        '-l', '--collapse-level', default=0, type=int,
        help='the min level to be collapsed, 0 to collapse all')
    parser.add_argument(
        '-b', '--bookmark', help='the bookmark file to be imported')
    parser.add_argument(
        '-p', '--pdf', help='the input PDF file')
    parser.add_argument(
        '-o', '--output-pdf', help='the output PDF file')

    args = parser.parse_args()

    if args.bookmark is None and args.pdf is None or \
            args.pdf is None and args.output_pdf is not None:
        parser.print_help(sys.stderr)
        return 1

    if args.bookmark is not None:
        with open(args.bookmark) as f:
            bookmarks = import_bmk(f.read(), args.collapse_level)
    else:
        pdftk_data = call(['pdftk', args.pdf, 'dump_data'], 'ascii')

        if args.format == 'pdftk':
            echo(pdftk_data, nl=False)

        bookmarks = import_pdftk(pdftk_data, args.collapse_level)

    if args.format == 'pdfmark' or (args.output_pdf is not None and args.pdf is not None):
        pdfmark = export_pdfmark(bookmarks)

    if args.format == 'json':
        echo(json.dumps(bookmarks))
    elif args.format == 'bmk':
        echo(export_bmk(bookmarks), nl=False)
    elif args.format == 'pdfmark':
        echo(pdfmark, nl=False)

    if args.output_pdf is not None:
        generate_pdf(pdfmark, args.pdf, args.output_pdf)

    return 0


if __name__ == '__main__':
    sys.exit(main())
