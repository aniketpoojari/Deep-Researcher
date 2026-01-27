"""LLM model loader with provider abstraction."""

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from utils.config_loader import ConfigLoader
from logger.logging import get_logger

logger = get_logger(__name__)


class ModelLoader:
    """Loader for LLM models with provider abstraction."""

    # Default models for each provider
    DEFAULT_MODELS = {
        "groq": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "openai": "gpt-5.2",
    }

    def __init__(self, provider: str = None):
        self.config = ConfigLoader()
        self._config_provider = self.config.get("llm.provider", "groq").lower()
        self.provider = (provider or self._config_provider).lower()
        self._llm = None
        logger.info(f"ModelLoader initialized (provider: {self.provider})")

    def _get_model_name(self, model_name: str = None) -> str:
        """Get the model name, using provider default if config doesn't match."""
        if model_name:
            return model_name
        # Only use config model_name if the config provider matches the active provider
        if self.provider == self._config_provider:
            return self.config.get("llm.model_name", self.DEFAULT_MODELS[self.provider])
        return self.DEFAULT_MODELS[self.provider]

    def load(self, model_name: str = None, temperature: float = None):
        """
        Load the LLM model.

        Args:
            model_name: Override model name from config
            temperature: Override temperature from config

        Returns:
            LangChain chat model instance
        """
        if self._llm:
            return self._llm

        if self.provider == "groq":
            self._llm = self._load_groq(model_name, temperature)
        elif self.provider == "openai":
            self._llm = self._load_openai(model_name, temperature)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}. Use 'groq' or 'openai'.")

        return self._llm

    def _load_groq(self, model_name: str = None, temperature: float = None) -> ChatGroq:
        """Load Groq model."""
        api_key = self.config.get_env("GROQ_API_KEY", default=None)
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env")

        model = self._get_model_name(model_name)
        temp = temperature if temperature is not None else self.config.get("llm.temperature", 0.1)

        logger.info(f"Loading Groq model: {model}")
        return ChatGroq(groq_api_key=api_key, model_name=model, temperature=temp)

    def _load_openai(self, model_name: str = None, temperature: float = None) -> ChatOpenAI:
        """Load OpenAI model."""
        api_key = self.config.get_env("OPENAI_API_KEY", default=None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in .env")

        model = self._get_model_name(model_name)
        temp = temperature if temperature is not None else self.config.get("llm.temperature", 0.1)

        logger.info(f"Loading OpenAI model: {model}")
        return ChatOpenAI(api_key=api_key, model=model, temperature=temp)
