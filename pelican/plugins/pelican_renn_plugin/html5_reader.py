import logging

from docutils.writers.html5_polyglot import HTMLTranslator, Writer

_LOGGER = logging.getLogger(__name__)


class PelicanHTML5Translator(HTMLTranslator):
    """
    Based on `pelican.readers.PelicanHTMLTranslator`, but uses docutils' HTML5
    translator instead.
    """

    def visit_abbreviation(self, node):
        attrs = {}
        if node.hasattr("explanation"):
            attrs["title"] = node["explanation"]
        self.body.append(self.starttag(node, "abbr", "", **attrs))

    def depart_abbreviation(self, node):
        del node  # Unused argument
        self.body.append("</abbr>")

    def visit_image(self, node):
        # set an empty alt if alt is not specified
        # avoids that alt is taken from src
        node["alt"] = node.get("alt", "")
        return super().visit_image(node)


class PelicanHTML5Writer(Writer):
    """
    Based on `pelican.readers.PelicanHTMLWriter`, but uses docutils' HTML5
    translator instead.
    """

    def __init__(self):
        super().__init__()
        self.translator_class = PelicanHTML5Translator


def patch_reader(readers):
    """
    Patch the RST reader to parse rst files into HTML5.

    :param readers: `Readers` instance.
    """

    reader = readers.reader_classes.get("rst")
    if not reader:
        _LOGGER.warning("renn: No 'rst' reader found")
        return

    _LOGGER.debug("renn: Patching rst reader for HTML5 support")
    # Replace the writer class with our own
    reader.writer_class = PelicanHTML5Writer
    # Monkey patch the field body translator base class with the HTML5 version
    reader.field_body_translator_class.__bases__ = (HTMLTranslator,)
