import re
from typing import Any, Dict, List, Optional
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import Agent, load_agent_prompt
from app.agents.storyteller import StorytellerAgent
from app.agents.grammarian import GrammarianAgent
from app.agents.quizzer import QuizzerAgent


class AgentType(Enum):
    """Available agent types that Moderator can delegate to."""
    STORYTELLER = "storyteller"
    GRAMMARIAN = "grammarian"
    QUIZZER = "quizzer"
    FINISH = "finish"


class ModeratorAgent(Agent):
    """
    The Moderator is the ONLY agent that communicates directly with the user.
    
    Responsibilities:
    - Accept user input (text or speech)
    - Route user requests to appropriate agents
    - Coordinate agent responses
    - Present results to user (text or speech)
    - Manage conversation flow
    - Provide a cohesive learning experience
    
    The Moderator acts as a language school coordinator, deciding which tool/agent
    is needed to best serve the user's learning goals.
    """
    
    def __init__(self, model: str = "gpt-4o"):
        super().__init__(model=model)
        
        # Initialize sub-agents
        self.storyteller = StorytellerAgent()
        self.grammarian = GrammarianAgent()
        self.quizzer = QuizzerAgent()
        
        # Router prompt - decides which agent to use
        self.router_prompt = ChatPromptTemplate.from_messages([
            ("system", load_agent_prompt("moderator")),
            ("placeholder", "{messages}"),
        ])
    
    async def run(self, user_input: str, user_level: str = "B1", user_theme: str = "Technology", user_language: str = "German") -> Dict[str, Any]:
        """
        Main entry point for user interaction with the language learning system.
        
        Args:
            user_input: User's input (text or transcribed speech)
            user_level: User's default language level
            user_theme: User's default theme
            user_language: User's target language
            db: Optional database session for direct story lookups
            current_user: Optional active user object for read-history tracking
            
        Returns:
            Dict with response to present to user and next action
        """
        # Store user context for extraction functions
        self.user_level = user_level
        self.user_theme = user_theme
        self.user_language = user_language
        
        try:
            if not await self.validate_input(user_input=user_input):
                return self._format_response(
                    False,
                    error="Invalid input. Please provide some text."
                )

            # Route the user request to the appropriate agent
            agent_decision = await self._route_request(user_input)
            
            if not agent_decision["success"]:
                return agent_decision
            
            # Get the agent to use and any parameters
            agent_type = agent_decision["agent"]
            params = agent_decision["parameters"]
            
            # Delegate to appropriate agent
            if agent_type == AgentType.STORYTELLER:
                result = await self.storyteller.run(**params)
                # Format story for user
                return await self._format_story_response(result)
            
            elif agent_type == AgentType.GRAMMARIAN:
                result = await self.grammarian.run(**params)
                # Format grammar feedback for user
                return await self._format_grammar_response(result)
            
            elif agent_type == AgentType.QUIZZER:
                result = await self.quizzer.run(**params)
                # Format quiz for user
                return await self._format_quiz_response(result)
            
            elif agent_type == AgentType.FINISH:
                return self._format_response(
                    success=True,
                    data={
                        "message": "Goodbye! Keep practicing and have a great language learning session! 👋",
                        "session_ended": True
                    }
                )
            
        except Exception as e:
            return self._format_response(
                False,
                error=f"Error processing request: {str(e)}"
            )
    
    async def validate_input(self, user_input: str, **kwargs) -> bool:
        """Validate user input."""
        if not user_input or len(user_input.strip()) == 0:
            return False
        return True
    
    
    async def _route_request(self, user_input: str) -> Dict[str, Any]:
        """
        Determine which agent to use based on user input.
        
        Returns routing decision with agent type and parameters.
        """
        try:
            chain = self.router_prompt | self.llm
            messages = [HumanMessage(content=user_input)]
            response = await chain.ainvoke({"messages": messages})
            
            # Parse the router's response
            decision_text = response.content.lower()
            
            # Extract agent type and parameters from the decision
            if "storyteller" in decision_text:
                params = await self._extract_story_params(user_input, decision_text)
                return {
                    "success": True,
                    "agent": AgentType.STORYTELLER,
                    "parameters": params
                }
            
            elif "grammarian" in decision_text:
                params = await self._extract_grammar_params(user_input)
                return {
                    "success": True,
                    "agent": AgentType.GRAMMARIAN,
                    "parameters": params
                }
            
            elif "quizzer" in decision_text:
                params = await self._extract_quiz_params(user_input, decision_text)
                return {
                    "success": True,
                    "agent": AgentType.QUIZZER,
                    "parameters": params
                }
            
            elif "finish" in decision_text or "goodbye" in decision_text:
                return {
                    "success": True,
                    "agent": AgentType.FINISH,
                    "parameters": {}
                }
            
            else:
                # Default to storyteller if unclear
                params = await self._extract_story_params(user_input, decision_text)
                return {
                    "success": True,
                    "agent": AgentType.STORYTELLER,
                    "parameters": params
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error routing request: {str(e)}"
            }
    
    async def _extract_story_params(self, user_input: str, decision_text: str) -> Dict[str, Any]:
        """Extract parameters for storyteller from user input and routing decision."""
        lower_input = user_input.lower()
        
        # Initialize with user defaults
        level = getattr(self, 'user_level', 'B1')
        theme = getattr(self, 'user_theme', 'Technology')
        language = getattr(self, 'user_language', 'German')
        
        # Try to extract level from user input (e.g., "A1", "B2", "C1")
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        for lvl in levels:
            if lvl.lower() in lower_input:
                level = lvl
                break
        
        # Extract theme if mentioned (e.g., "about technology", "on history")
        if "about " in lower_input:
            theme_start = lower_input.find("about ") + 6
            theme_text = user_input[theme_start:].strip()
            if theme_text:
                # Take first few words after "about"
                theme = " ".join(theme_text.split()[:3])
        elif "on " in lower_input:
            theme_start = lower_input.find("on ") + 3
            theme_text = user_input[theme_start:].strip()
            if theme_text:
                theme = " ".join(theme_text.split()[:3])
        
        # Extract target language if mentioned
        supported_languages = ["French", "Spanish", "German", "English", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Mandarin"]
        for lang in supported_languages:
            if f"in {lang.lower()}" in lower_input or f"{lang.lower()}" in lower_input:
                language = lang
                break

        return {
            "level": level,
            "theme": theme,
            "language": language
        }
    
    async def _extract_grammar_params(self, user_input: str) -> Dict[str, Any]:
        """Extract parameters for grammarian from user input."""
        level = getattr(self, 'user_level', 'B1')
        return {
            "text": user_input,
            "language_level": level
        }
    
    async def _extract_quiz_params(self, user_input: str, decision_text: str) -> Dict[str, Any]:
        """Extract parameters for quizzer from user input."""
        level = getattr(self, 'user_level', 'B1')
        # Placeholder - would need story context in real implementation
        return {
            "story_content": "Sample story content here",
            "level": level,
            "question_count": 5
        }
    
    async def _format_story_response(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format storyteller response for user presentation."""
        if not agent_result["success"]:
            return agent_result
        
        story = agent_result["data"]["story"]
        language = agent_result["data"].get("language")
        return self._format_response(
            success=True,
            data={
                "type": "story",
                "language": language,
                "story": {
                    "title": story["title"],
                    "content": story["content"],
                    "level": story["level"],
                    "theme": story["theme"],
                },
                "instruction": "Read the story and reflect on what you learned."
            }
        )
    
    async def _format_grammar_response(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format grammarian response for user presentation."""
        if not agent_result["success"]:
            return agent_result
        
        analysis = agent_result["data"]["analysis"]
        return self._format_response(
            success=True,
            data={
                "type": "grammar_feedback",
                "analysis": analysis,
                "next_step": "Verstehen Sie die Erklärung? Möchten Sie mehr Beispiele?"
            }
        )
    
    async def _format_quiz_response(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format quizzer response for user presentation."""
        if not agent_result["success"]:
            return agent_result
        
        quiz = agent_result["data"]["quiz"]
        return self._format_response(
            success=True,
            data={
                "type": "quiz",
                "quiz_content": quiz,
                "instruction": "Beantworten Sie die Fragen bitte!"
            }
        )
