from typing import Any, Dict
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import Agent, load_agent_prompt


class GrammarianAgent(Agent):
    """
    The GrammarianAgent analyzes and explains grammar for a target language.
    
    Responsibilities:
    - Correct user input for grammar errors
    - Explain grammar rules (cases, verb placement, etc.)
    - Analyze generated content for grammar quality
    - Provide learning-focused explanations
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model=model)
        self.correction_prompt = ChatPromptTemplate.from_messages([
            ("system", load_agent_prompt("grammarian_correction")),
            ("human", "Check and explain the grammar in this text:\n\n{text}")
        ])
    
    async def run(self, text: str, language_level: str = "B1") -> Dict[str, Any]:
        """
        Analyze and correct text for grammar errors.
        
        Args:
            text: The text to analyze
            language_level: User's language level for contextual explanations
            
        Returns:
            Dict with corrections and explanations
        """
        try:
            if not await self.validate_input(text=text):
                return self._format_response(False, error="Invalid text input")
            
            chain = self.correction_prompt | self.llm
            response = await chain.ainvoke({
                "text": text,
                "level": language_level
            })
            
            # Parse response
            response_text = response.content
            
            return self._format_response(
                success=True,
                data={
                    "original_text": text,
                    "analysis": response_text,
                    "level": language_level
                }
            )
            
        except Exception as e:
            return self._format_response(
                success=False,
                error=f"Error analyzing grammar: {str(e)}"
            )
    
    async def validate_input(self, text: str, **kwargs) -> bool:
        """Validate input text."""
        if not text or len(text.strip()) < 2:
            return False
        return True
    
    async def explain_rule(self, rule: str, example: str) -> Dict[str, Any]:
        """
        Explain a specific German grammar rule with examples.
        
        Args:
            rule: The grammar rule to explain (e.g., "dative case")
            example: Example sentence
            
        Returns:
            Explanation and additional examples
        """
        try:
            explanation_prompt = ChatPromptTemplate.from_messages([
                ("system", load_agent_prompt("grammarian_explanation")),
                ("human", "Explain the rule: {rule}\n\nExample: {example}")
            ])
            
            chain = explanation_prompt | self.llm
            response = await chain.ainvoke({
                "rule": rule,
                "example": example
            })
            
            return self._format_response(
                success=True,
                data={
                    "rule": rule,
                    "explanation": response.content
                }
            )
            
        except Exception as e:
            return self._format_response(
                success=False,
                error=f"Error explaining rule: {str(e)}"
            )