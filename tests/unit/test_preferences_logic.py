from backend.agents.preferences import PreferencesAgent


class TestRuleBasedParse:
    def setup_method(self):
        self.agent = PreferencesAgent()

    def _parse(self, text):
        return self.agent._rule_based_parse(text)

    def test_vegan(self):
        dietary, *_ = self._parse("I'm vegan")
        assert "vegan" in dietary

    def test_vegetarian(self):
        dietary, *_ = self._parse("vegetarian options please")
        assert "vegetarian" in dietary

    def test_gluten_free(self):
        dietary, *_ = self._parse("I need gluten free food")
        assert "gluten-free" in dietary

    def test_halal(self):
        dietary, *_ = self._parse("halal restaurants only")
        assert "halal" in dietary

    def test_kosher(self):
        dietary, *_ = self._parse("we keep kosher")
        assert "kosher" in dietary

    def test_lactose_free(self):
        dietary, *_ = self._parse("lactose intolerant")
        assert "lactose-free" in dietary

    def test_multiple_dietary_restrictions(self):
        dietary, *_ = self._parse("I'm vegetarian and gluten intolerant")
        assert "vegetarian" in dietary
        assert "gluten-free" in dietary
        assert len(dietary) == 2

    def test_no_dietary_keywords(self):
        dietary, *_ = self._parse("I like museums and jazz")
        assert dietary == []

    def test_case_insensitive(self):
        dietary, *_ = self._parse("VEGAN and HALAL please")
        assert "vegan" in dietary
        assert "halal" in dietary

    def test_wheelchair(self):
        _, access, *_ = self._parse("wheelchair access needed")
        assert access == "wheelchair_accessible"

    def test_disability(self):
        _, access, *_ = self._parse("I have a disability")
        assert access == "wheelchair_accessible"

    def test_accessible(self):
        _, access, *_ = self._parse("accessible venues preferred")
        assert access == "wheelchair_accessible"

    def test_no_accessibility(self):
        _, access, *_ = self._parse("I love hiking and adventure")
        assert access == "none"

    def test_dietary_and_accessibility(self):
        dietary, access, *_ = self._parse("I'm vegan and need wheelchair access")
        assert "vegan" in dietary
        assert access == "wheelchair_accessible"

    def test_remaining_fields_are_empty(self):
        result = self._parse("vegan wheelchair accessible")
        dietary, access, attr_hints, gastro_hints, transport_hints, general = result
        assert attr_hints == ""
        assert gastro_hints == ""
        assert transport_hints == ""
        assert general == ""

    def test_empty_input(self):
        dietary, access, *_ = self._parse("")
        assert dietary == []
        assert access == "none"

    def test_no_duplicate_tags(self):
        dietary, *_ = self._parse("vegan food, vegan restaurant, vegan desserts")
        assert dietary.count("vegan") == 1
