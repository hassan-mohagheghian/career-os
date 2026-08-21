"""Tests for CityNormalizer — canonical city+country extraction."""

from cities.domain.entities.city import CityNormalizer


class TestCityNormalizer:
    def test_known_city_maps_to_country(self):
        assert CityNormalizer.normalize("Berlin") == ("Berlin", "Germany")
        assert CityNormalizer.normalize("berlin") == ("Berlin", "Germany")
        assert CityNormalizer.normalize("Paris") == ("Paris", "France")
        assert CityNormalizer.normalize("London") == ("London", "UK")

    def test_alias_collapses_to_canonical_name(self):
        assert CityNormalizer.normalize("München") == ("Munich", "Germany")
        assert CityNormalizer.normalize("Köln") == ("Cologne", "Germany")
        assert CityNormalizer.normalize("Wien") == ("Vienna", "Austria")
        assert CityNormalizer.normalize("Zürich") == ("Zurich", "Switzerland")

    def test_city_comma_country(self):
        assert CityNormalizer.normalize("Berlin, Germany") == ("Berlin", "Germany")
        assert CityNormalizer.normalize("Amsterdam, Netherlands") == ("Amsterdam", "Netherlands")

    def test_city_region_country_takes_last_as_country(self):
        assert CityNormalizer.normalize("Frankfurt am Main, Hesse, Germany") == ("Frankfurt", "Germany")

    def test_slash_separated_takes_first(self):
        assert CityNormalizer.normalize("Berlin / Munich") == ("Berlin", "Germany")

    def test_country_only(self):
        assert CityNormalizer.normalize("Germany") == ("", "Germany")
        assert CityNormalizer.normalize("Netherlands") == ("", "Netherlands")
        assert CityNormalizer.normalize("UK") == ("", "UK")

    def test_remote(self):
        assert CityNormalizer.normalize("Remote") == ("Remote", "")
        assert CityNormalizer.normalize("Remote Germany") == ("Remote", "Germany")

    def test_unknown_single_token_title_cased(self):
        assert CityNormalizer.normalize("nowhereville") == ("Nowhereville", "")

    def test_empty(self):
        assert CityNormalizer.normalize("") == ("", "")
        assert CityNormalizer.normalize(None) == ("", "")