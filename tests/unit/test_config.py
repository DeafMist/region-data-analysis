"""Unit tests for config module."""

import pytest
from config import get_region_config, set_region


class TestConfig:
    """Tests for configuration functions."""

    def test_get_region_config_belgorod(self):
        config = get_region_config("belgorod")
        assert config["name"] == "Белгородская область"
        assert config["code_hh"] == 1817
        assert config["code_trudvsem"] == "3100000000000"

    def test_get_region_config_default(self):
        config = get_region_config()
        assert config["name"] == "Белгородская область"

    def test_get_region_config_unknown(self):
        with pytest.raises(ValueError, match="Unknown region: unknown"):
            get_region_config("unknown")

    def test_set_region(self):
        set_region("belgorod")
        from config import CURRENT_REGION

        assert CURRENT_REGION == "belgorod"

    def test_set_region_unknown(self):
        with pytest.raises(ValueError, match="Unknown region: unknown"):
            set_region("unknown")
