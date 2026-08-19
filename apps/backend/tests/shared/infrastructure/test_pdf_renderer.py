"""Tests for the markdown → PDF renderer."""

from __future__ import annotations

from shared.infrastructure.pdf_renderer import MarkdownPdfRenderer


class TestMarkdownPdfRenderer:
    def test_renders_pdf_bytes(self):
        pdf = MarkdownPdfRenderer().render("# Hassan\n\nSenior Engineer\n\n- Python\n- Kafka")
        assert isinstance(pdf, bytes)
        assert pdf.startswith(b"%PDF")
        assert pdf.rstrip().endswith(b"%%EOF")

    def test_renders_with_title(self):
        pdf = MarkdownPdfRenderer().render("body", title="Tailored Resume")
        assert pdf.startswith(b"%PDF")

    def test_handles_typographic_unicode_characters(self):
        content = "# Staff Engineer \u2014 Berlin\n\nSenior \u201cengineer\u201d \u2022 Python \u2026"
        pdf = MarkdownPdfRenderer().render(content)
        assert pdf.startswith(b"%PDF")

    def test_strips_non_latin1_characters(self):
        content = "Hello \u2014 caf\u00e9 \u20ac \u4f60\u597d"
        pdf = MarkdownPdfRenderer().render(content)
        assert pdf.startswith(b"%PDF")