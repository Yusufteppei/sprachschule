"""
Base Agent class that all agents inherit from.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
import os

from langchain_openai import ChatOpenAI
from app.core.config import settings


def load_agent_prompt(prompt_name: str) -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / f"{prompt_name}.txt"
    return prompt_path.read_text(encoding="utf-8")


class Agent(ABC):
    """
    Abstract base class for all agents.
    
    All agents share:
    - A language model (LLM)
    - Input validation
    - Output formatting
    """
    
    def __init__(self, model: str = "gpt-4o-mini", language: str = "any"):
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

        self.llm = ChatOpenAI(model=model)
        self.language = language
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's task.
        
        Returns:
            Dict with 'success' bool, 'data' containing the result, and optional 'error'
        """
        pass
    
    async def validate_input(self, **kwargs) -> bool:
        """Override in subclasses for specific validation."""
        return True
    
    def _format_response(self, success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
        """Standard response format for all agents."""
        return {
            "success": success,
            "agent": self.name,
            "data": data,
            "error": error
        }
