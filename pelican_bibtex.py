"""
Pelican BibTeX
==============

A Pelican plugin that populates the context with a list of formatted
citations, loaded from a BibTeX file at a configurable path.

The use case for now is to generate a ``Publications'' page for academic
websites.
"""

# Fork author: Emmanuel Fleury <emmanuel.fleury@gmail.com>
# Initial author: Vlad Niculae <vlad@vene.ro>
# Unlicense (see UNLICENSE for details)

import logging
LOGGER = logging.getLogger(__name__)

from pelican import signals

__version__ = '0.3'

def get_field(entry, field):
    """
    Get a field in an entry.
    """
    return entry.fields.get(field) if field in entry.fields.keys() else ""


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
        'article'       : (5, 'Journal Articles'),
        'inproceedings' : (6, 'Papers'),
        'conference'    : (7, 'Papers'),
        'phdthesis'     : (8, 'PhD Thesis'),
        'mastersthesis' : (9, 'Master Thesis'),
        'techreport'    : (10, 'Technical Report'),
        'manual'        : (11, 'Manual'),
        'misc'          : (12, 'Other Publications'),
        'unpublished'   : (13, 'Unpublished'),
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
        LOGGER.warn('`pelican_bibtex` failed to load dependency `pybtex`')
        return

    try:
        bib_items = Parser().parse_file(generator.settings['PUBLICATIONS_SRC'])
    except PybtexError as err:
        LOGGER.warn('`pelican_bibtex` failed to parse file %s: %s',
                    generator.settings['PUBLICATIONS_SRC'],
                    str(err))
        return

    publications = []

    for fmt_entry in plain.Style().format_entries(bib_items.entries.values()):
        key = fmt_entry.key
        entry = bib_items.entries[key]

        # Render the bibtex string for the entry
        buf = StringIO()
        Writer().write_stream(BibliographyData(entries={key: entry}), buf)

        # Prettify BibTeX entries
        text = fmt_entry.text.render(html.Backend())
        text = text.replace(r"\{", "").replace(r"\}", "")
        text = text.replace("{", "").replace("}", "")

        publications.append({'bibtex' : buf.getvalue(),
                             'doi'    : get_field(entry, 'doi'),
                             'entry'  : entrytype(entry.type),
                             'key'    : key,
                             'pdf'    : get_field(entry, 'pdf'),
                             'poster' : get_field(entry, 'poster'),
                             'slides' : get_field(entry, 'slides'),
                             'text'   : text,
                             'url'    : get_field(entry, 'url'),
                             'note'    : get_field(entry, 'note'),
                             'year'   : entry.fields.get('year'),
                             'authorizer': get_field(entry, 'authorizer'),
                             })

    generator.context['publications'] = publications


def register():
    """
    Register the signal to the Pelican framework.
    """
    signals.generator_init.connect(add_publications)
