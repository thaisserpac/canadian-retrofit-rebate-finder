from app.services.rebate_service import extract_province, extract_retrofit_types


class TestExtractProvince:
    def test_full_name(self):
        assert extract_province("I live in Ontario") == "ON"

    def test_abbreviation(self):
        assert extract_province("I'm in BC") == "BC"

    def test_city(self):
        assert extract_province("I'm a homeowner in Calgary") == "AB"

    def test_city_montreal(self):
        assert extract_province("We live in Montreal") == "QC"

    def test_case_insensitive(self):
        assert extract_province("nova scotia resident") == "NS"

    def test_no_match_with_fallback(self):
        assert extract_province("I want a heat pump", "ON") == "ON"

    def test_no_match_no_fallback(self):
        assert extract_province("I want a heat pump") is None

    def test_multi_word_province(self):
        assert extract_province("Prince Edward Island homeowner here") == "PE"

    def test_pei_abbreviation(self):
        assert extract_province("I'm from PEI") == "PE"


class TestExtractRetrofitTypes:
    def test_heat_pump(self):
        types = extract_retrofit_types("I want to install a heat pump")
        assert "heat_pump_air_source" in types
        assert "heat_pump_ground_source" in types

    def test_specific_type(self):
        types = extract_retrofit_types("thinking about geothermal heating")
        assert types == ["heat_pump_ground_source"]

    def test_insulation(self):
        types = extract_retrofit_types("need better insulation")
        assert "insulation_attic" in types
        assert "insulation_wall" in types
        assert "insulation_basement" in types

    def test_multiple_types(self):
        types = extract_retrofit_types("windows and solar panels")
        assert "windows_doors" in types
        assert "solar_panels" in types

    def test_no_match(self):
        types = extract_retrofit_types("hello, how are you?")
        assert types == []

    def test_mini_split(self):
        types = extract_retrofit_types("a ductless mini-split system")
        assert "heat_pump_mini_split" in types

    def test_smart_thermostat(self):
        types = extract_retrofit_types("smart thermostat upgrade")
        assert "smart_thermostat" in types

    def test_air_sealing(self):
        types = extract_retrofit_types("my house is very drafty")
        assert "air_sealing" in types
