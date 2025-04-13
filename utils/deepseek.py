import yaml
import pathlib
import requests
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage


class DeepSeekTranslator:
    """
    A translation utility using DeepSeek API for translating text from a source language to a target language.
    """

    def __init__(
        self,
        api_key: str = "",
        endpoint: str = "",
        model: str = "",
        source_language: str = "",
        target_language: str = "",
        system_prompt: str = "",
        config_path: str = "config/deepseek.yml",
    ):
        """
        Initialize the translator with optional parameters or a YAML config file.

        Args:
            api_key (str): API key for DeepSeek.
            endpoint (str): API endpoint.
            model (str): Model name to use.
            source_language (str): Language to translate from.
            target_language (str): Language to translate to.
            system_prompt (str): Custom system prompt template.
            config_path (str): Path to YAML config file.
        Raises:
            ValueError: If required values are missing.
        """
        # Load config file if it exists
        config = {}
        config_file = pathlib.Path(config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

        # Use provided arguments or fallback to config
        self._api_key = api_key or config.get("api_key", "")
        self._endpoint = endpoint or config.get("endpoint", "")
        self._model = model or config.get("model", "")
        self.source_lang = source_language or config.get("system_prompt", {}).get(
            "variables", {}
        ).get("source_language", "")
        self.target_lang = target_language or config.get("system_prompt", {}).get(
            "variables", {}
        ).get("target_language", "")
        self.system_prompt_template = system_prompt or config.get(
            "system_prompt", {}
        ).get("description", "")

        # Validate required fields
        if not all([self._api_key, self._endpoint, self._model]):
            raise ValueError("API key, endpoint, and model are required.")
        if not self.system_prompt_template:
            raise ValueError("A valid system prompt template is required.")
        if (
            "{source_language}" in self.system_prompt_template
            and self.source_lang == ""
        ):
            raise ValueError("Source language must be specified in the system prompt.")
        if (
            "{target_language}" in self.system_prompt_template
            and self.target_lang == ""
        ):
            raise ValueError("Target language must be specified in the system prompt.")

        # Format system prompt with languages
        self._update_prompt()
        self.clear_chat_history()

        # Set up openai client
        self._client = OpenAI(api_key=self._api_key, base_url=self._endpoint)

    def _update_prompt(self):
        """Internal method to update the formatted system prompt."""
        if (
            "{source_language}" in self.system_prompt_template
            and "{target_language}" in self.system_prompt_template
        ):
            self.system_prompt = self.system_prompt_template.format(
                source_language=self.source_lang, target_language=self.target_lang
            )
        else:
            if "{source_language}" in self.system_prompt_template:
                self.system_prompt = self.system_prompt_template.format(
                    source_language=self.source_lang
                )
            if "{target_language}" in self.system_prompt_template:
                self.system_prompt = self.system_prompt_template.format(
                    target_language=self.target_lang
                )

    def set_source_language(self, lang: str):
        """Set a new source language and update the system prompt."""
        self.source_lang = lang
        self._update_prompt()
        self.clear_chat_history()

    def set_target_language(self, lang: str):
        """Set a new target language and update the system prompt."""
        self.target_lang = lang
        self._update_prompt()
        self.clear_chat_history()

    def get_chat_history(self):
        """Return the current chat history, including the system prompt."""
        return self._chat_history

    def update_chat_history(self, hist: dict | list[dict] | ChatCompletionMessage):
        """
        Append message(s) to the chat history.

        Args:
            hist (dict or list): Message(s) to add, each must be a dict with 'role' and 'content'.
        """
        if isinstance(hist, dict):
            self._chat_history.append(hist)
        elif isinstance(hist, list):
            if not all(isinstance(h, dict) for h in hist):
                raise TypeError("Each chat history item must be a dictionary.")
            self._chat_history.extend(hist)
        elif isinstance(hist, ChatCompletionMessage):
            self._chat_history.append({"role": hist.role, "content": hist.content})
        else:
            raise TypeError(
                "Chat history must be a dictionary, list of dictionaries or instance of ChatCompletionMessage."
            )

    def clear_chat_history(self):
        """Reset the chat history to include only the system prompt."""
        self._chat_history = [{"role": "system", "content": self.system_prompt}]

    def get_translation_history(self) -> list[str]:
        """Return the current translation history."""
        translation_history = []
        for message in self._chat_history:
            if message["role"] == "assistant":
                translation_history.extend(message["content"].split("\\n"))
        return translation_history

    def translate(self, text: str | list[str]) -> str | list[str]:
        """
        Translate the given text using DeepSeek API.

        Args:
            text (str) | list[str]: The input text to translate.

        Returns:
            str: The translated text.
        """
        assert type(text) in [str, list], "text must be str or list"

        if type(text) == list:
            self.update_chat_history({"role": "user", "content": "\\n".join(text)})
        else:
            self.update_chat_history({"role": "user", "content": text})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=self._chat_history,  # pyright: ignore
            stream=False,
        )
        self.update_chat_history(response.choices[0].message)
        translated_content = response.choices[0].message.content
        if type(text) == list:
            translated_content = translated_content.split("\\n")
        return translated_content
