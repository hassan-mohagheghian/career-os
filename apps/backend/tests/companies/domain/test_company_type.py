"""Tests for the company_type fixed vocabulary + normalization."""

from companies.domain.company_type import (
    VALID_COMPANY_TYPES,
    normalize_company_type,
)


class TestValidCompanyTypes:
    def test_contains_only_fixed_types(self):
        assert set(VALID_COMPANY_TYPES) == {
            "PRODUCT_COMPANY",
            "RECRUITING_AGENCY",
            "STAFFING_COMPANY",
            "CONSULTING_COMPANY",
            "UNKNOWN",
        }


class TestNormalizeCompanyType:
    def test_passthrough_valid_uppercase(self):
        for value in VALID_COMPANY_TYPES:
            assert normalize_company_type(value) == value

    def test_lowercase_is_uppercased(self):
        assert normalize_company_type("staffing_company") == "STAFFING_COMPANY"
        assert normalize_company_type("recruiting_agency") == "RECRUITING_AGENCY"
        assert normalize_company_type("consulting company") == "UNKNOWN"

    def test_invalid_is_coerced_to_unknown(self):
        assert normalize_company_type("bogus") == "UNKNOWN"
        assert normalize_company_type("product") == "UNKNOWN"
        assert normalize_company_type("  random thing  ") == "UNKNOWN"

    def test_empty_and_none_map_to_none(self):
        assert normalize_company_type(None) is None
        assert normalize_company_type("") is None
        assert normalize_company_type("   ") is None