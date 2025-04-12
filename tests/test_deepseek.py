import pytest
from unittest.mock import patch, mock_open, MagicMock
from utils.deepseek import DeepSeekTranslator


# Sample YAML config content
mock_yaml = """
api_key: test_api_key
endpoint: https://api.deepseek.com/chat
model: deepseek-chat
system_prompt:
  description: "Translate from {source_language} to {target_language}."
  variables:
    source_language: "English"
    target_language: "Thai"
"""


@pytest.fixture
def valid_translator():
    with patch("builtins.open", mock_open(read_data=mock_yaml)), patch(
        "pathlib.Path.exists", return_value=True
    ):
        return DeepSeekTranslator(config_path="fake_config.yml")


def test_init_success(valid_translator):
    assert valid_translator.api_key == "test_api_key"
    assert valid_translator.endpoint.startswith("https")
    assert valid_translator.model == "deepseek-chat"
    assert valid_translator.source_lang == "English"
    assert valid_translator.target_lang == "Thai"
    assert "Translate from" in valid_translator.system_prompt


def test_missing_required_fields():
    with patch("builtins.open", mock_open(read_data="")), patch(
        "pathlib.Path.exists", return_value=False
    ):
        with pytest.raises(
            ValueError, match="API key, endpoint, and model are required."
        ):
            DeepSeekTranslator(api_key="", endpoint="", model="")


def test_set_languages_updates_prompt(valid_translator):
    valid_translator.set_source_language("French")
    assert "French" in valid_translator.system_prompt
    valid_translator.set_target_language("Japanese")
    assert "Japanese" in valid_translator.system_prompt


def test_chat_history_methods(valid_translator):
    valid_translator.clear_chat_history()
    initial = valid_translator.get_chat_history()
    assert initial[0]["role"] == "system"

    valid_translator.update_chat_history({"role": "user", "content": "Hello"})
    valid_translator.update_chat_history(
        [
            {"role": "assistant", "content": "สวัสดี"},
            {"role": "user", "content": "How are you?"},
        ]
    )
    history = valid_translator.get_chat_history()
    assert len(history) == 4

    with pytest.raises(TypeError):
        valid_translator.update_chat_history("Not a dict")


@patch("requests.post")
def test_translate_success(mock_post, valid_translator):
    mock_post.return_value = MagicMock(status_code=200)
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "สวัสดี"}}]
    }

    result = valid_translator.translate("Hello")
    assert result == "สวัสดี"
    assert valid_translator.get_chat_history()[-1]["content"] == "สวัสดี"
    assert mock_post.called
