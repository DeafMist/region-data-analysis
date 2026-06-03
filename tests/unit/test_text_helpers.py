"""Unit tests for text_helpers module."""

from utils.text_helpers import (
    extract_employer_base_name,
    extract_city_from_address,
    match_names,
)


class TestExtractEmployerBaseName:
    """Tests for extract_employer_base_name function."""

    def test_extract_ooo(self):
        assert extract_employer_base_name("ООО Ромашка") == "Ромашка"
        assert extract_employer_base_name('ООО "Ромашка"') == "Ромашка"

    def test_extract_ao(self):
        assert extract_employer_base_name("АО Технологии") == "Технологии"

    def test_extract_ip(self):
        assert extract_employer_base_name("ИП Иванов") == "Иванов"

    def test_extract_mbou(self):
        assert extract_employer_base_name("МБОУ СОШ №1") == "СОШ №1"

    def test_empty_or_none(self):
        assert extract_employer_base_name(None) == ""
        assert extract_employer_base_name("") == ""

    def test_no_legal_form(self):
        assert extract_employer_base_name("Ромашка") == "Ромашка"


class TestExtractCityFromAddress:
    """Tests for extract_city_from_address function."""

    def test_extract_belgorod(self):
        assert extract_city_from_address("г. Белгород, ул. Победы, 85") == "Белгород"
        assert extract_city_from_address("Белгород, ул. Победы") == "Белгород"

    def test_extract_stary_oskol(self):
        assert (
            extract_city_from_address("г. Старый Оскол, ул. Ленина") == "Старый Оскол"
        )

    def test_extract_gubkin(self):
        assert extract_city_from_address("Губкин, ул. Мира") == "Губкин"

    def test_extract_rakiinoe(self):
        assert extract_city_from_address("п. Ракитное, ул. Центральная") == "Ракитное"

    def test_none_or_empty(self):
        assert extract_city_from_address(None) is None
        assert extract_city_from_address("") is None

    def test_no_city_match(self):
        assert extract_city_from_address("неизвестная улица, дом 1") is None


class TestMatchNames:
    """Tests for match_names function."""

    def test_exact_match(self):
        assert match_names("Сбербанк", "Сбербанк") is True
        assert match_names("ВТБ", "ВТБ") is True

    def test_partial_match(self):
        assert match_names("Сбербанк", "Сбербанк России") is True
        assert match_names("Магнит", "ООО Магнит") is True

    def test_match_with_legal_form(self):
        assert match_names("ООО Ромашка", "Ромашка") is True
        assert match_names("Ромашка", "АО Ромашка") is True

    def test_no_match(self):
        assert match_names("Сбербанк", "ВТБ") is False
        assert match_names("Магнит", "Пятёрочка") is False

    def test_none_values(self):
        assert match_names(None, "Сбербанк") is False
        assert match_names("Сбербанк", None) is False
        assert match_names(None, None) is False
