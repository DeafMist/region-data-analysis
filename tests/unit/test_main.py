"""Unit tests for main module."""

from unittest.mock import patch, MagicMock
from main import main


class TestMain:
    """Tests for main entry point."""

    @patch("main.Pipeline")
    @patch("main.set_region")
    @patch("main.argparse.ArgumentParser")
    def test_main_trudvsem(self, mock_parser, mock_set_region, mock_pipeline):
        mock_args = MagicMock()
        mock_args.region = "belgorod"
        mock_args.parser = "trudvsem"
        mock_parser.return_value.parse_args.return_value = mock_args

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run.return_value = True
        mock_pipeline.return_value = mock_pipeline_instance

        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)

    @patch("main.Pipeline")
    @patch("main.set_region")
    @patch("main.argparse.ArgumentParser")
    def test_main_hh(self, mock_parser, mock_set_region, mock_pipeline):
        mock_args = MagicMock()
        mock_args.region = "belgorod"
        mock_args.parser = "hh"
        mock_parser.return_value.parse_args.return_value = mock_args

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run.return_value = True
        mock_pipeline.return_value = mock_pipeline_instance

        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(0)

    @patch("main.Pipeline")
    @patch("main.set_region")
    @patch("main.argparse.ArgumentParser")
    def test_main_failure(self, mock_parser, mock_set_region, mock_pipeline):
        mock_args = MagicMock()
        mock_args.region = "belgorod"
        mock_args.parser = "trudvsem"
        mock_parser.return_value.parse_args.return_value = mock_args

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run.return_value = False
        mock_pipeline.return_value = mock_pipeline_instance

        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)
