# PDF-Bookmark

Import and export pdf bookmark with the `bmk` format.

## Command

```
usage: pdf_bookmark.py [-h] [-f {bmk,none,pdftk,pdfmark,json}]
                       [-l COLLAPSE_LEVEL] [-b BOOKMARK] [-p PDF]
                       [-o OUTPUT_PDF]

Import and export PDF bookmark

optional arguments:
  -h, --help            show this help message and exit
  -f {bmk,none,pdftk,pdfmark,json}, --format {bmk,none,pdftk,pdfmark,json}
                        the output format of bookmark
  -l COLLAPSE_LEVEL, --collapse-level COLLAPSE_LEVEL
                        the min level to be collapsed, 0 to collapse all
  -b BOOKMARK, --bookmark BOOKMARK
                        the bookmark file to be imported
  -p PDF, --pdf PDF     the input PDF file
  -o OUTPUT_PDF, --output-pdf OUTPUT_PDF
                        the output PDF file
```
