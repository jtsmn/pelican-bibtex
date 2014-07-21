"""
Pelican BibTeX
==============

A Pelican plugin that populates the context with a list of formatted
citations, loaded from a BibTeX file at a configurable path.

The use case for now is to generate a ``Publications'' page for academic
websites.
"""
# Author: Vlad Niculae <vlad@vene.ro>
# Unlicense (see UNLICENSE for details)

import logging
logger = logging.getLogger(__name__)

from pelican import signals

__version__ = '0.3'


def entrytype(label):
    """
    Define a ranking among the different types of publication and a
    collection of labels to be displayed for each entrytype.
    """
    entries = {
        'book'          : (0, 'Book'),
        'incollection'  : (1, 'Book in a Collection'),
        'booklet'       : (2, 'Booklet'),
        'proceedings'   : (3, 'Proceedings'),
        'inbook'        : (4, 'Chapter in a Book'),
        'article'       : (5, 'Journal'),
        'inproceedings' : (6, 'Conference'),
        'phdthesis'     : (7, 'PhD Thesis'),
        'masterthesis'  : (8, 'Master Thesis'),
        'techreport'    : (9, 'Technical Report'),
        'manual'        : (10, 'Manual'),
        'misc'          : (11, 'Miscellaneous'),
        'unpublished'   : (12, 'Unpublished'),
    }

    if label in entries:
        return entries[label]
    else:
        return (100, label)

def add_publications(generator):
    """
    Populates context with a list of BibTeX publications.

    Configuration
    -------------
    generator.settings['PUBLICATIONS_SRC']:
        local path to the BibTeX file to read.

    Output
    ------
    generator.context['publications']:
        List of tuples (key, year, text, bibtex, pdf, slides, poster).
        See Readme.md for more details.
    """
    if 'PUBLICATIONS_SRC' not in generator.settings:
        return
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO
    try:
        from pybtex.database.input.bibtex import Parser
        from pybtex.database.output.bibtex import Writer
        from pybtex.database import BibliographyData, PybtexError
        from pybtex.backends import html
        from pybtex.style.formatting import plain
    except ImportError:
        logger.warn('`pelican_bibtex` failed to load dependency `pybtex`')
        return

    refs_file = generator.settings['PUBLICATIONS_SRC']
    try:
        bibdata_all = Parser().parse_file(refs_file)
    except PybtexError as e:
        logger.warn('`pelican_bibtex` failed to parse file %s: %s' % (
            refs_file,
            str(e)))
        return

    publications = []

    # format entries
    plain_style = plain.Style()
    html_backend = html.Backend()
    formatted_entries = plain_style.format_entries(bibdata_all.entries.values())

    for formatted_entry in formatted_entries:
        key = formatted_entry.key
        entry = bibdata_all.entries[key]
        type = entry.type
        year = entry.fields.get('year')
        pdf = entry.fields.pop('pdf', None)
        slides = entry.fields.pop('slides', None)
        poster = entry.fields.pop('poster', None)

        #render the bibtex string for the entry
        bib_buf = StringIO()
        bibdata_this = BibliographyData(entries={key: entry})
        Writer().write_stream(bibdata_this, bib_buf)
        text = formatted_entry.text.render(html_backend)
        doi = entry.fields.get('doi') if 'doi' in entry.fields.keys() else ""
        url = entry.fields.get('url') if 'url' in entry.fields.keys() else ""

        # Prettify BibTeX entries
        text = text.replace("\{", "")
        text = text.replace("{", "")
        text = text.replace("\}", "")
        text = text.replace("}", "")

        publications.append({'entry'  : entrytype(type),
                             'key'    : key,
                             'year'   : year,
                             'text'   : text,
                             'doi'    : doi,
                             'url'    : url,
                             'bibtex' : bib_buf.getvalue(),
                             'pdf'    : pdf,
                             'slides' : slides,
                             'poster' : poster})

    generator.context['publications'] = publications


def register():
    signals.generator_init.connect(add_publications)
