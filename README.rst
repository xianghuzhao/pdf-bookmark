PDF-Bookmark
============

PDF-Bookmark is a tool for import and export pdf bookmark
with the ``bmk`` format.


``bmk`` format
--------------

The ``bmk`` format is used to describe the bookmark of a pdf file.
It can be used to import bookmark into a pdf file.

``bmk`` format is easy to write.
It looks quite like the content of a book.
So you can copy the content and modify from it.

Each line represents a bookmark item. The title and the page number are
separated by more than 4 dots ("``.``").

The level of a bookmark is specified by the indentation of spaces.
The default indentation is 2 spaces, and it could be configured
with special statement.

Unicode titles are supported. Please make sure the file is saved with
UTF-8 encoding.

This is a simple example of a ``bmk`` file. ::

    序................1
    Chapter 1................4
    Chapter 2................5
      2.1 Section 1................6
        2.1.1 SubSection 1................6
        2.1.2 SubSection 2................8
      2.2 Section 2................12
    Chapter 3................20
    Appendix................36

Import the bookmark and create a new pdf file::

    $ pdf_bookmark.py -p input.pdf -b bookmark.bmk -o new.pdf


Special statements
^^^^^^^^^^^^^^^^^^

There could also be special statements in the file to do more controls
on the bookmark. These statements start with ``!!!`` and modify some
properties of bookmark. The new property will affect bookmarks after
the line until it is changed again.

It is normal that the main body of a pdf file does not start from the
first page, and the page number is not always arabic. ::

    !!! num_style = Roman
    Preface................I
    Content................IV

    !!! new_index = 12
    !!! num_style = Arabic
    Introduction................1
    Chapter 1................4
    Chapter 2................5
      2.1 Section 1................6
      2.2 Section 2................7
    Chapter 3................10
    Appendix................11


Export ``bmk`` format
^^^^^^^^^^^^^^^^^^^^^

The ``bmk`` file could also be exported from a pdf file with bookmark.
You may also modify the bookmark from the exported one. ::

    $ pdf_bookmark.py -p input.pdf


Prerequisite
------------

``pdf-bookmark`` utilize
`PDFtk <https://www.pdflabs.com/tools/pdftk-server/>`_
and `Ghostscript <https://www.ghostscript.com>`_
to export and import pdf bookmarks.
They must be installed before running ``pdf-bookmark``.


PDFtk
^^^^^

PDFtk is used here to export bookmark from pdf file.
The java port `pdftk-java <https://gitlab.com/pdftk-java/pdftk>`_
may also be OK.

On Arch Linux, ``pdftk-java`` could be installed by::

    $ sudo pacman -S pdftk java-commons-lang

Verify the installation::

    $ pdftk --version


Ghostscript
^^^^^^^^^^^

Ghostscript is used here to import bookmark to pdf file.

On Arch Linux, it could be installed by::

    $ sudo pacman -S ghostscript

Verify the installation::

    $ gs --version


Command
-------

::

    usage: pdf-bookmark [-h] [-f {bmk,none,pdftk,pdfmark,json}]
                        [-l COLLAPSE_LEVEL] [-b BOOKMARK] [-p PDF] [-o OUTPUT_PDF]

    Import and export PDF bookmark

    optional arguments:
      -h, --help            show this help message and exit
      -f {bmk,none,pdftk,pdfmark,json}, --format {bmk,none,pdftk,pdfmark,json}
                            the output format of bookmark
      -l COLLAPSE_LEVEL, --collapse-level COLLAPSE_LEVEL
                            the min level to be collapsed, 0 to expand all
      -b BOOKMARK, --bookmark BOOKMARK
                            the bookmark file to be imported
      -p PDF, --pdf PDF     the input PDF file
      -o OUTPUT_PDF, --output-pdf OUTPUT_PDF
                            the output PDF file


Example
-------

Change the collapse level
^^^^^^^^^^^^^^^^^^^^^^^^^

::

    $ pdf_bookmark.py -p input.pdf -l 2 -o new.pdf


Statement
---------
