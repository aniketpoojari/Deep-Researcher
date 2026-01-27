"""LLM model loader with provider abstraction."""

from email.policy import default
from langchain_groq import ChatGroq
from utils.config_loader import ConfigLoader
from logger.logging import get_logger

logger = get_logger(__name__)


class ModelLoader:
    """Loader for LLM models with provider abstraction."""

    # Default models for each provider
    DEFAULT_MODELS = {
        "groq": "meta-llama/llama-4-maverick-17b-128e-instruct",
    }

    def __init__(self, provider: str = None):
        self.config = ConfigLoader()
        # Use provider from config if not specified
        self.provider = (provider or self.config.get("llm.provider", "groq")).lower()
        self._llm = None
        logger.info(f"ModelLoader initialized (provider: {self.provider})")

    def load(self, model_name: str = None, temperature: float = None) -> ChatGroq:
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
        else:
            raise ValueError(f"Unsupported provider: {self.provider}. Use 'groq'.")

        return self._llm

    def _load_groq(self, model_name: str = None, temperature: float = None) -> ChatGroq:
        """Load Groq model."""
        api_key = self.config.get_env("GROQ_API_KEY", default=None)
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env")

        model = model_name or self.config.get("llm.model_name", self.DEFAULT_MODELS["groq"])
        temp = temperature if temperature is not None else self.config.get("llm.temperature", 0.1)

        logger.info(f"Loading Groq model: {model}")
        return ChatGroq(groq_api_key=api_key, model_name=model, temperature=temp)
