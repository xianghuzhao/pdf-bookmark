#!/usr/bin/env python
#
# Copyright (C) 2011-2013 W. Trevor King <wking@drexel.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

"""Merge PDFs preserving bookmarks.

Thanks to Larry Cai for suggesting that Unicode be supported and for
discussion about the `--pdfmarks` option.
"""

import codecs as _codecs
import locale as _locale
import os as _os
import os.path as _os_path
import re as _re
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile


__version__ = '0.3'


PDFTK = 'pdftk'
GS = 'gs'


def invoke(args, stdout=None, encoding=None):
    """
    >>> invoke(['echo', 'hi', 'there'])
    b'hi there\\n'
    >>> invoke(['this command does not exist'])
    Traceback (most recent call last):
      ...
    OSError: [Errno 2] No such file or directory: 'this command does not exist'
    """
    P = _subprocess.PIPE
    capture_stdout = stdout is None
    if capture_stdout:
        stdout = P
    p = _subprocess.Popen(
        args, stdin=P, stdout=stdout, stderr=_sys.stderr, shell=False, cwd='.')
    stdout_,stderr_ = p.communicate()
    status = p.wait()
    assert status == 0, status
    if encoding:
        stdout_ = str(stdout_, encoding)
    return stdout_


class BookmarkedPDF (object):
    _UNICODE_REGEXP = _re.compile('&#([0-9]+);')

    def __init__(self, filename=None, encoding='ascii'):
        self.filename = filename
        self.encoding = encoding
        if self.filename:
            self.get_bookmarks()

    def get_bookmarks(self):
        data = invoke(
            [PDFTK, self.filename, 'dump_data'], encoding=self.encoding)
        self.pages,self.bookmarks = self._parse_dump_data(data)

    @staticmethod
    def _unicode_replace_match(match):
        return chr(int(match.group(1)))

    @classmethod
    def _unicode_replace(self, string):
        r"""
        >>> BookmarkedPDF._unicode_replace('&#945;&#946;&#947;')
        '\u03b1\u03b2\u03b3'
        """
        return self._UNICODE_REGEXP.sub(self._unicode_replace_match, string)

    @classmethod
    def _parse_dump_data(self, data):
        r"""
        >>> from pprint import pprint
        >>> data = '\n'.join([
        ...     'InfoBegin',
        ...     'InfoKey: CreationDate',
        ...     'InfoValue: D:20080502020302Z',
        ...     'NumberOfPages: 123',
        ...     'BookmarkBegin',
        ...     'BookmarkTitle: Chapter 1',
        ...     'BookmarkLevel: 1',
        ...     'BookmarkPageNumber: 1',
        ...     'BookmarkTitle: Section 1.1',
        ...     'BookmarkLevel: 2',
        ...     'BookmarkPageNumber: 2',
        ...     'BookmarkTitle: Section 1.1.1',
        ...     'BookmarkLevel: 3',
        ...     'BookmarkPageNumber: 3',
        ...     'BookmarkTitle: Section 1.1.2',
        ...     'BookmarkLevel: 3',
        ...     'BookmarkPageNumber: 4',
        ...     'BookmarkTitle: &#945;&#946;&#947;',
        ...     'BookmarkLevel: 4',
        ...     'BookmarkPageNumber: 4',
        ...     'BookmarkTitle: Section 1.2',
        ...     'BookmarkLevel: 2',
        ...     'BookmarkPageNumber: 5',
        ...     'PageLabelBegin',
        ...     'PageLabelNewIndex: 1',
        ...     'PageLabelStart: 316',
        ...     'PageLabelPrefix:',
        ...     'PageLabelNumStyle: DecimalArabicNumerals',
        ...     'PageLabelNewIndex: 2',
        ...     'PageLabelStart: 317',
        ...     'PageLabelPrefix:',
        ...     'PageLabelNumStyle: DecimalArabicNumerals',
        ...     'PageLabelNewIndex: 3',
        ...     'PageLabelStart: 318',
        ...     'PageLabelPrefix:',
        ...     'PageLabelNumStyle: DecimalArabicNumerals',
        ...     'PageLabelNewIndex: 4',
        ...     ])
        >>> pages,bookmarks = BookmarkedPDF._parse_dump_data(data)
        >>> pages
        123
        >>> pprint(bookmarks)  # doctest: +REPORT_UDIFF
        [{'level': 1, 'page': 1, 'title': 'Chapter 1'},
         {'level': 2, 'page': 2, 'title': 'Section 1.1'},
         {'level': 3, 'page': 3, 'title': 'Section 1.1.1'},
         {'level': 3, 'page': 4, 'title': 'Section 1.1.2'},
         {'level': 4, 'page': 4, 'title': '\u03b1\u03b2\u03b3'},
         {'level': 2, 'page': 5, 'title': 'Section 1.2'}]
        """
        pages = None
        bookmarks = []
        bookmark_info = {}
        bookmark_info_fields = ['title', 'level', 'page']
        for line in data.splitlines():
            try:
                key,value = line.split(': ', 1)
            except ValueError:  # e.g. line == 'InfoBegin'
                continue
            if key == 'NumberOfPages':
                pages = int(value)
            elif key.startswith('Bookmark'):
                k = key[len('Bookmark'):].lower()
                if k in ['level', 'pagenumber']:
                    if k == 'pagenumber':
                        k = 'page'
                    value = int(value)
                elif k == 'title':
                    if self._UNICODE_REGEXP.search(value):
                        value = self._unicode_replace(value)
                bookmark_info[k] = value
                ready_for_bookmark = True
                for field in bookmark_info_fields:
                    if field not in bookmark_info:
                        ready_for_bookmark = False
                        break
                if ready_for_bookmark:
                    bookmarks.append(bookmark_info)
                    bookmark_info = {}
        return (pages, bookmarks)

def generate_pdfmarks(inputs=(), title=None, author=None, keywords=None):
    r"""
    >>> inputs = []
    >>> for pages,bookmarks in [
    ...         (1,
    ...          [{'level': 1, 'page': 1, 'title': 'Table of Contents'}]),
    ...         (100,
    ...          [{'level': 1, 'page': 1, 'title': 'Chapter 1'},
    ...           {'level': 2, 'page': 2, 'title': 'Section 1.1'},
    ...           {'level': 3, 'page': 3, 'title': 'Section 1.1.1'},
    ...           {'level': 3, 'page': 4, 'title': 'Section 1.1.2'},
    ...           {'level': 4, 'page': 4, 'title': '\u03b1\u03b2\u03b3'},
    ...           {'level': 2, 'page': 5, 'title': 'Section 1.2'}]),
    ...         (100,
    ...          [{'level': 1, 'page': 1, 'title': 'Chapter 2'},
    ...           {'level': 2, 'page': 2, 'title': 'Section 2.1'},
    ...           {'level': 3, 'page': 3, 'title': 'Section 2.1.1'},
    ...           {'level': 3, 'page': 4, 'title': 'Section 2.1.2'},
    ...           {'level': 4, 'page': 4, 'title': '\u03b1\u03b2\u03b3'},
    ...           {'level': 2, 'page': 5, 'title': 'Section 2.2'}]),
    ...         ]:
    ...     pdf = BookmarkedPDF()
    ...     pdf.pages = pages
    ...     pdf.bookmarks = bookmarks
    ...     inputs.append(pdf)
    >>> print(generate_pdfmarks(inputs=inputs, title='My Book',
    ...     author='Myself', keywords=['fun', 'witty', 'interesting']))
    ... # doctest: +REPORT_UDIFF
    [ /Title (My Book)
      /Author (Myself)
      /Keywords (fun, witty, interesting)
      /DOCINFO pdfmark
    [ /Title (Table of Contents) /Page 1 /OUT pdfmark
    [ /Title (Chapter 1) /Page 2 /Count -2 /OUT pdfmark
    [ /Title (Section 1.1) /Page 3 /Count -2 /OUT pdfmark
    [ /Title (Section 1.1.1) /Page 4 /OUT pdfmark
    [ /Title (Section 1.1.2) /Page 5 /Count -1 /OUT pdfmark
    [ /Title <FEFF03B103B203B3> /Page 5 /OUT pdfmark
    [ /Title (Section 1.2) /Page 6 /OUT pdfmark
    [ /Title (Chapter 2) /Page 102 /Count -2 /OUT pdfmark
    [ /Title (Section 2.1) /Page 103 /Count -2 /OUT pdfmark
    [ /Title (Section 2.1.1) /Page 104 /OUT pdfmark
    [ /Title (Section 2.1.2) /Page 105 /Count -1 /OUT pdfmark
    [ /Title <FEFF03B103B203B3> /Page 105 /OUT pdfmark
    [ /Title (Section 2.2) /Page 106 /OUT pdfmark
    <BLANKLINE>
    """
    pdfmarks = []
    if title or author or keywords:
        docinfo = []
        if title:
            docinfo.append('/Title {}'.format(_pdfmark_unicode(title)))
        if author:
            docinfo.append('/Author {}'.format(_pdfmark_unicode(author)))
        if keywords:
            docinfo.append('/Keywords {}'.format(_pdfmark_unicode(
                        ', '.join(keywords))))
        docinfo.append('/DOCINFO pdfmark')
        pdfmarks.append('[ {}' .format('\n  '.join(docinfo)))
    bookmarks = []
    startpage = 0
    for pdf in inputs:
        for bookmark in pdf.bookmarks:
            mark = dict(bookmark)  # shallow copy
            mark['page'] += startpage
            bookmarks.append(mark)
        startpage += pdf.pages
    for i,bookmark in enumerate(bookmarks):
        attributes = [
            '/Title {}'.format(_pdfmark_unicode(bookmark['title'])),
            '/Page {}'.format(bookmark['page']),
            #'[/XYZ null null null]',  # preserve page zoom and viewport
            ]
        count = 0
        for bmk in bookmarks[i+1:]:
            if bmk['level'] == bookmark['level']:
                break
            if bmk['level'] == bookmark['level'] + 1:
                count += 1
        if count:
            attributes.append('/Count -{}'.format(count))
        pdfmarks.append('[ {} /OUT pdfmark'.format(' '.join(attributes)))
    pdfmarks.append('')  # terminal newline
    return '\n'.join(pdfmarks)


def _write_pdfmark_noop_file(encoding='ascii'):
    # By default, Ghostscript will preserve pdfmarks from the sources PDFs
    fd,filename = _tempfile.mkstemp(prefix='pdfmark-noop-', text=True)
    # Make `[... /OUT pdfmark` a no-op.
    _os.write(fd, """
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
""".encode(encoding))
    _os.close(fd)
    return filename

def _write_pdfmark_restore_file(encoding='ascii'):
    fd,filename = _tempfile.mkstemp(prefix='pdfmark-restore-', text=True)
    # Restore the default `[... /Out pdfmark` behaviour
    _os.write(fd, '/pdfmark { originalpdfmark } bind def\n'.encode(encoding))
    _os.close(fd)
    return filename

def _pdfmark_unicode(string):
    r"""
    >>> _pdfmark_unicode('ascii text with ) paren')
    '(ascii text with \\) paren)'
    >>> _pdfmark_unicode('\u03b1\u03b2\u03b3')
    '<FEFF03B103B203B3>'
    """
    try:
        ascii = string.encode('ascii')
    except UnicodeEncodeError:
        b = _codecs.BOM_UTF16_BE + string.encode('utf-16-be')
        return '<{}>'.format(''.join('{:02X}'.format(byte) for byte in b))
    else:
        # escape special characters
        for a,b in [('\\', '\\\\'), ('(', '\\('), (')', '\\)'),
                    ('\n', '\\n'), ('\t', '\\t')]:
            string = string.replace(a, b)
        return '({})'.format(string)

def _pdfmark_unicode_decode(string):
    r"""
    >>> _pdfmark_unicode_decode(_pdfmark_unicode('\u03b1\u03b2\u03b3'))
    '\u03b1\u03b2\u03b3'
    """
    assert string.startswith('<FEFF'), string
    assert string.endswith('>'), string
    b = bytes(int(float.fromhex(x1+x2))
              for x1,x2 in zip(string[5:-2:2], string[6:-1:2]))
    return str(b, 'utf-16-be')

def _write_markfile(pdfmarks, pause_for_manual_tweaking=False,
                    encoding='ascii'):
    fd,filename = _tempfile.mkstemp(prefix='pdfmarks-', text=True)
    if pdfmarks:
        _os.write(fd, pdfmarks.encode(encoding))
    _os.close(fd)
    if pause_for_manual_tweaking:
        print('edit {} as you see fit, and press enter when ready'.format(
                filename))
        _sys.stdin.readline()
    return filename

def merge_pdfs(inputs, output, pdfmarks=None,
               pause_for_manual_tweaking=False, encoding='ascii'):
    args = [GS, '-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite']
    if output:
        args.append('-sOutputFile={}'.format(output))
    else:
        args.extend(['-sOutputFile=-', '-q'])
    if pdfmarks:
        mark_noop = _write_pdfmark_noop_file(encoding=encoding)
        args.append(mark_noop)
    args.extend([pdf.filename for pdf in inputs])
    if pdfmarks:
        mark_restore = _write_pdfmark_restore_file(
            encoding=encoding)
        args.append(mark_restore)
    markfile = _write_markfile(
        pdfmarks=pdfmarks, pause_for_manual_tweaking=pause_for_manual_tweaking,
        encoding=encoding)
    args.append(markfile)
    print('preparing to execute: {}'.format(args))
    invoke(args, stdout=_sys.stdout)
    if pdfmarks:
        _os.unlink(mark_noop)
        _os.unlink(mark_restore)
    _os.unlink(markfile)


if __name__ == '__main__':
    import argparse

    encoding = _locale.getpreferredencoding(do_setlocale=True)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', metavar='PDF', nargs='+',
                        help='an input PDF to merge')
    parser.add_argument(
        '-v', '--version', action='version',
        version='%(prog)s {}'.format(__version__))
    parser.add_argument('--ask', dest='pause_for_manual_tweaking',
                        action='store_const', const=True,
                        help='pause for manual pdfmark tweaking')
    parser.add_argument('--output', dest='output', default='output.pdf',
                        help='name of the output PDF')
    parser.add_argument('--title', dest='title',
                        help='title of output PDF')
    parser.add_argument('--author', dest='author',
                        help='author of output PDF')
    parser.add_argument('--keyword', metavar='KEYWORD', dest='keywords',
                        action='append',
                        help='keywords for the output PDF')
    parser.add_argument('--pdftk', dest='pdftk', default=PDFTK,
                        help='path to the pdftk executable')
    parser.add_argument('--gs', dest='gs', default=GS,
                        help='path to the gs (Ghostscript) executable')
    parser.add_argument('--pdfmarks', dest='pdfmarks',
                        help=('path to pdfmarks file.  If not given, a '
                              'temporary file is used.  If given and the file '
                              'is missing, execution will stop after the file '
                              'is created (before the Ghostscript run).  If '
                              'given and the file exists, no attempt will be '
                              'make to use pdftk to generate the mark file (I '
                              'assume your input file is what you want).'))
    parser.add_argument('--unicode', dest='convert_unicode_strings',
                        action='store_const', const=True,
                        help=('instead of merging PDFs, convert '
                              'PDF-formatted unicode strings.  For example '
                              "`--unicode '<FEFF03B103B203B3>' "
                              '\u03b1\u03b2\u03b3`'))

    args = parser.parse_args()

    PDFTK = args.pdftk
    GS = args.gs

    if args.convert_unicode_strings:
        for string in args.input:
            if string.startswith('<FEFF'):
                alt = _pdfmark_unicode_decode(string)
            else:
                alt = _pdfmark_unicode(string)
            print('{} -> {}'.format(string, alt))
        _sys.exit(0)

    inputs = []
    for filename in args.input:
        inputs.append(BookmarkedPDF(filename))
    if args.pdfmarks and _os_path.isfile(args.pdfmarks):
        pdfmarks = _codecs.open(args.pdfmarks, 'r', encoding).read()
    else:
        pdfmarks = generate_pdfmarks(
            inputs, title=args.title, author=args.author,
            keywords=args.keywords)
        if args.pdfmarks:
            _codecs.open(args.pdfmarks, 'w', encoding).write(pdfmarks)
            _sys.exit(0)
    merge_pdfs(inputs=inputs, pdfmarks=pdfmarks, output=args.output,
               pause_for_manual_tweaking=args.pause_for_manual_tweaking,
               encoding=encoding)
