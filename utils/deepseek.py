import yaml
import pathlib
import openai
import time
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from deepseek_tokenizer import ds_token


class DeepSeekTranslator:
    """
    A translation utility using DeepSeek API for translating text from a source language to a target language.
    """

    def __init__(
        self,
        api_key: str = "",
        endpoint: str = "",
        context_length: int = 0,
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
            context_length (int): Context length for the model.
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
        self._context_length = context_length or config.get("context_length", 0)
        self.source_lang = source_language or config.get("system_prompt", {}).get(
            "variables", {}
        ).get("source_language", "")
        self.target_lang = target_language or config.get("system_prompt", {}).get(
            "variables", {}
        ).get("target_language", "")
        self._constraint_prompt = config.get("system_prompt", {}).get("constraint", "")
        if self._constraint_prompt == "":
            raise ValueError("Constraint prompt is required.")
        self._description_prompt = system_prompt or config.get("system_prompt", {}).get(
            "description", ""
        )
        self.system_prompt_template = self._constraint_prompt + self._description_prompt

        # Validate required fields
        if not all([self._api_key, self._endpoint, self._model, self._context_length]):
            raise ValueError(
                "API key, endpoint, model, and context length are required."
            )
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
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._endpoint if "openai" not in self._endpoint else None,
        )

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

    def _count_tokens(self, messages: list) -> int:
        """Count the total tokens in the list of chat messages."""
        return sum(len(ds_token.encode(msg["content"])) for msg in messages)

    def translate(self, text: str | list[str]) -> str | list[str]:
        """
        Translate the given text using DeepSeek API.

        Args:
            text (str) | list[str]: The input text to translate.

        Returns:
            str: The translated text.
        """
        assert type(text) in [str, list], "text must be str or list"

        new_input = "\\n".join(text) if isinstance(text, list) else text
        new_message = {"role": "user", "content": new_input}

        # Add new input temporarily to test total token count
        temp_history = self._chat_history + [new_message]
        total_tokens = self._count_tokens(temp_history)

        # Trim history if total tokens exceed model limit
        while total_tokens > self._context_length and len(self._chat_history) > 1:
            self._chat_history.pop(0)  # Remove oldest message
            temp_history = self._chat_history + [new_message]
            total_tokens = self._count_tokens(temp_history)

        # Finally update the chat history with current message
        self.update_chat_history(new_message)

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._chat_history,  # pyright: ignore
                stream=False,
            )
        except openai.APIStatusError as e:
            if e.status_code == 402:
                print("You have run out of balance.")
                exit(1)
            elif e.status_code == 429:
                print("You have reached the rate limit.")
                time.sleep(5)
                return self.translate(text)
            elif e.status_code in [500, 503]:
                print("Server error. Retrying in 5 seconds...")
                time.sleep(5)
                return self.translate(text)
            else:
                print(f"Unhandled API error: {e}")
                self.clear_chat_history()
                return self.translate(text)

        self.update_chat_history(response.choices[0].message)
        translated_content = response.choices[0].message.content
        if isinstance(text, list):
            # FIX: hallucination issue (output lines are not same as input lines)
            translated_content = translated_content.split("\\n")
        return translated_content
