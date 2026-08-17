import json
from unittest.mock import patch, MagicMock
from scraper_engine.cli import main
from scraper_engine.http import HTTPResponse


def test_cli_stdout(capsys):
    config = {
        "name": "test_cli",
        "steps": [
            {
                "id": "step1",
                "request": {
                    "url": "https://example.com"
                },
                "fields": {
                    "title": {
                        "selector": "h1",
                        "selector_type": "css",
                        "type": "text"
                    }
                }
            }
        ]
    }
    json_str = json.dumps(config)

    mock_resp = HTTPResponse(status_code=200, text="<html><body><h1>Test Title</h1></body></html>")

    with patch("httpx.Client.send", return_value=MagicMock(status_code=200, text=mock_resp.text, headers={})) as _:
        exit_code = main([json_str])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data == [{"title": "Test Title"}]


def test_cli_output_file(tmp_path):
    config = {
        "name": "test_cli_file",
        "steps": [
            {
                "id": "step1",
                "request": {
                    "url": "https://example.com"
                },
                "fields": {
                    "title": {
                        "selector": "h1",
                        "selector_type": "css",
                        "type": "text"
                    }
                }
            }
        ]
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    output_file = tmp_path / "out.json"

    mock_resp = HTTPResponse(status_code=200, text="<html><body><h1>Test Title</h1></body></html>")

    with patch("httpx.Client.send", return_value=MagicMock(status_code=200, text=mock_resp.text, headers={})) as _:
        exit_code = main([str(config_file), "-o", str(output_file)])
        assert exit_code == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data == [{"title": "Test Title"}]


def test_cli_invalid_config(capsys):
    exit_code = main(["{invalid_json}"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error executing scraper" in captured.err
