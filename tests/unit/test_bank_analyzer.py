"""Unit tests for bank_analyzer."""

import pandas as pd
from analyzers.bank_analyzer import BankAnalyzer, is_bank_verified


class TestIsBankVerified:
    """Tests for is_bank_verified function."""

    def test_exact_match(self, sample_cbr_df):
        assert is_bank_verified("СБЕРБАНК РОССИИ", sample_cbr_df) is True
        assert is_bank_verified("ВТБ", sample_cbr_df) is True

    def test_partial_match(self, sample_cbr_df):
        assert is_bank_verified("Сбербанк", sample_cbr_df) is True
        assert is_bank_verified("Сбер", sample_cbr_df) is True

    def test_no_match(self, sample_cbr_df):
        assert is_bank_verified("Несуществующий банк", sample_cbr_df) is False

    def test_empty_name(self, sample_cbr_df):
        assert is_bank_verified(None, sample_cbr_df) is False
        assert is_bank_verified("", sample_cbr_df) is False

    def test_empty_cbr_df(self):
        empty_df = pd.DataFrame(columns=["bank_name"])
        assert is_bank_verified("Сбербанк", empty_df) is False


class TestBankAnalyzer:
    """Tests for BankAnalyzer class."""

    def setup_method(self):
        self.analyzer = BankAnalyzer(region="test_region")

    def test_analyze_basic_stats(self, sample_banks_df):
        result = self.analyzer.analyze(sample_banks_df)

        assert result is not None
        assert result.iloc[0]["total_banks"] == 3
        assert result.iloc[0]["total_atms"] == 1
        assert result.iloc[0]["unique_banks"] == 3

    def test_analyze_with_cbr_verification(self, sample_banks_df, sample_cbr_df):
        result = self.analyzer.analyze(sample_banks_df, cbr_df=sample_cbr_df)

        assert result.iloc[0]["verified_banks_count"] > 0
        assert "Сбербанк" in str(result.iloc[0]["verified_banks_list"])

    def test_analyze_empty_dataframe(self):
        result = self.analyzer.analyze(pd.DataFrame())
        assert result.empty

    def test_analyze_saves_csv_files(self, sample_banks_df, tmp_path):
        original_get_path = self.analyzer._get_output_path

        def mock_get_path(filename):
            return str(tmp_path / filename)

        self.analyzer._get_output_path = mock_get_path

        self.analyzer.analyze(sample_banks_df)

        banks_dist_file = tmp_path / "test_region_banks_distribution.csv"
        assert banks_dist_file.exists()

        self.analyzer._get_output_path = original_get_path
