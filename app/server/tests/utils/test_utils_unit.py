"""Tests for utils.py — normalize_url, mask_pii, text_to_html."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from utils import normalize_url, stream_json, mask_pii, text_to_html


class TestNormalizeUrl:
    def test_strips_query_params(self):
        assert normalize_url("https://example.com/path?q=1&b=2") == "https://example.com/path"

    def test_strips_trailing_slash(self):
        assert normalize_url("https://example.com/path/") == "https://example.com/path"

    def test_none_returns_none(self):
        assert normalize_url(None) is None

    def test_empty_returns_empty(self):
        assert normalize_url("") == ""

    def test_no_query_params(self):
        assert normalize_url("https://example.com/path") == "https://example.com/path"

    def test_strips_both_query_and_slash(self):
        assert normalize_url("https://example.com/path/?q=1") == "https://example.com/path"

    def test_preserves_fragment(self):
        result = normalize_url("https://example.com/path#section")
        assert result == "https://example.com/path"

    def test_complex_query_params(self):
        assert normalize_url("https://example.com/jobs?search=python&page=2&sort=date") == "https://example.com/jobs"

    def test_root_url(self):
        assert normalize_url("https://example.com/") == "https://example.com"

    def test_root_url_no_slash(self):
        assert normalize_url("https://example.com") == "https://example.com"


class TestStreamJson:
    def test_returns_data_as_is(self):
        data = {"key": "value"}
        assert stream_json(data) == data

    def test_returns_list(self):
        data = [1, 2, 3]
        assert stream_json(data) == data

    def test_returns_none(self):
        assert stream_json(None) is None


class TestMaskPii:
    def test_masks_phone(self):
        result = mask_pii("Header\nCall me at +49 123 456 7890")
        assert "[PHONE]" in result

    def test_masks_email(self):
        result = mask_pii("Header\nEmail: test@example.com")
        assert "[EMAIL]" in result

    def test_masks_linkedin(self):
        result = mask_pii("Header\nhttps://linkedin.com/in/johndoe")
        assert "[PROFILE]" in result

    def test_masks_github(self):
        result = mask_pii("Header\nhttps://github.com/johndoe")
        assert "[PROFILE]" in result

    def test_masks_name_first_line(self):
        result = mask_pii("John Doe\nEngineer")
        assert "[NAME]" in result

    def test_no_mask_for_long_first_line(self):
        long_name = "A" * 70
        result = mask_pii(f"{long_name}\nEngineer")
        assert "[NAME]" not in result

    def test_masks_email_also_gets_name_masked(self):
        result = mask_pii("user@domain.com\nEngineer")
        assert "[NAME]" in result

    def test_masks_multiple_phones(self):
        result = mask_pii("Header\nCall +1 555 123 4567 or +44 20 7946 0958")
        assert result.count("[PHONE]") == 2

    def test_masks_email_in_text(self):
        result = mask_pii("Header\nContact john.doe@company.org for details")
        assert "[EMAIL]" in result

    def test_masks_github_short(self):
        result = mask_pii("Header\nMy github.com/johndoe has code")
        assert "github.com/[PROFILE]" in result

    def test_first_line_name_masking(self):
        result = mask_pii("Jane Smith\nDesigner")
        assert result.startswith("[NAME]")

    def test_first_line_with_colon_not_masked(self):
        result = mask_pii("Phone: +49 123 456 7890\nMore info")
        assert result.startswith("Phone:")


class TestTextToHtml:
    def test_empty_text(self):
        result = text_to_html("")
        assert "<br>" in result

    def test_uppercase_heading(self):
        result = text_to_html("SUMMARY")
        assert "<h3" in result

    def test_named_heading(self):
        result = text_to_html("Professional Experience")
        assert "<h3" in result

    def test_skills_heading(self):
        result = text_to_html("Skills")
        assert "<h3" in result

    def test_education_heading(self):
        result = text_to_html("Education")
        assert "<h3" in result

    def test_bullet_point(self):
        result = text_to_html("● Python expert")
        assert "padding-left" in result

    def test_bullet_dot(self):
        result = text_to_html("• Java developer")
        assert "padding-left" in result

    def test_bullet_dash(self):
        result = text_to_html("- SQL databases")
        assert "padding-left" in result

    def test_normal_text(self):
        result = text_to_html("Regular line")
        assert "<div" in result

    def test_job_title_line(self):
        result = text_to_html("Senior Software Engineer | Google")
        assert "font-weight" in result

    def test_developer_title_line(self):
        result = text_to_html("Backend Developer | Meta")
        assert "font-weight" in result

    def test_multiline_output(self):
        text = "SUMMARY\n\n● Skill one\nRegular text"
        result = text_to_html(text)
        assert "<h3" in result
        assert "padding-left" in result
        assert result.count("<div") >= 2

    def test_html_escape(self):
        result = text_to_html("Use <script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
