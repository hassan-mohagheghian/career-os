"""Markdown → PDF rendering for generated application documents.

Converts markdown content to a styled PDF (A4) using ``markdown`` for the
HTML conversion and ``fpdf2``'s ``write_html`` for the layout. fpdf2 is a
self-contained, pure-Python PDF writer with no system library dependencies,
so export works in any environment.

fpdf2's built-in core fonts (Helvetica etc.) only cover Latin-1, so before
rendering we transliterate typographic / non-Latin-1 characters (em-dashes,
curly quotes, bullets, ellipses, ...) to ASCII to avoid a
``FPDFUnicodeEncodingException``.
"""

from __future__ import annotations

from fpdf import FPDF
from markdown import markdown as md_to_html

PAGE_W = 210
PAGE_H = 297
MARGIN = 16

_DEFAULT_MARKDOWN_EXTENSIONS = ["extra", "sane_lists"]

_TRANSLIT = str.maketrans(
    {
        "\u00a0": " ",
        "\u2010": "-",  # hyphen
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2015": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201a": "'",
        "\u201b": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201f": '"',
        "\u2022": "-",  # bullet
        "\u2026": "...",
        "\u20ac": "EUR",
    }
)


def _normalize_text(text: str) -> str:
    """Make ``text`` safe for a Latin-1 PDF font."""
    text = text.translate(_TRANSLIT)
    # Replace any remaining character outside Latin-1 with a safe placeholder.
    return "".join(ch if ord(ch) <= 0xFF else "?" for ch in text)


class MarkdownPdfRenderer:
    """Render markdown text to an A4 PDF byte string."""

    def render(self, markdown_text: str, title: str = "") -> bytes:
        markdown_text = _normalize_text(markdown_text)
        title = _normalize_text(title)
        html = md_to_html(markdown_text, extensions=_DEFAULT_MARKDOWN_EXTENSIONS)
        pdf = FPDF(unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.add_page()
        pdf.set_font("Helvetica", "", 10)

        if title:
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 7, title)
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(3)

        pdf.write_html(html)
        return bytes(pdf.output())


__all__ = ["MarkdownPdfRenderer"]