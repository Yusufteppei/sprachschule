"""
Main entry point for the language learning agent system.

This demonstrates how the modular agent system works together:
1. User interacts only with ModeratorAgent
2. ModeratorAgent coordinates all other agents
3. Each agent handles its specific domain
"""

from app.agents.moderator import ModeratorAgent
from app.agents.storyteller import StorytellerAgent, MockStoryteller
from app.agents.grammarian import GrammarianAgent
from app.agents.quizzer import QuizzerAgent


class LanguageLearningSystem:
    """
    Main system that orchestrates the language learning agents.
    
    Usage:
        system = LanguageLearningSystem()
        response = await system.process_user_input("Erzählen Sie mir eine Geschichte auf B1 Niveau")
    """
    
    def __init__(self, use_mock_storyteller: bool = False):
        """
        Initialize the language learning system.
        
        Args:
            use_mock_storyteller: If True, uses mock storyteller for testing
                                 If False, uses real LLM-based storyteller
        """
        self.moderator = ModeratorAgent()
        
        # Optionally use mock storyteller for testing
        if use_mock_storyteller:
            self.moderator.storyteller = MockStoryteller()
    
    async def process_user_input(self, user_input: str) -> dict:
        """
        Process user input and return response.
        
        This is the main entry point for user interaction.
        The moderator will decide which agent to use and present results.
        
        Args:
            user_input: User's input text or transcribed speech
            
        Returns:
            Response dict with the appropriate content to show user
        """
        return await self.moderator.run(user_input)
    
    async def process_story_request(self, level: str, theme: str) -> dict:
        """
        Request a story directly (bypassing moderator routing).
        Useful for testing specific components.
        """
        return await self.moderator.storyteller.run(level=level, theme=theme)
    
    async def process_grammar_request(self, text: str, level: str = "B1") -> dict:
        """
        Request grammar correction directly (bypassing moderator routing).
        """
        return await self.moderator.grammarian.run(text=text, language_level=level)
    
    async def process_quiz_request(self, story_content: str, level: str, question_count: int = 5) -> dict:
        """
        Request a quiz directly (bypassing moderator routing).
        """
        return await self.moderator.quizzer.run(
            story_content=story_content,
            level=level,
            question_count=question_count
        )


# Example usage and workflow
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Example workflow for the language learning system."""
        
        # Initialize system
        system = LanguageLearningSystem(use_mock_storyteller=True)
        
        # Workflow: User wants a story, reads it, gets a quiz, corrects grammar
        workflow = [
            "Erzählen Sie mir eine B1-Level Geschichte über Technologie",
            "Ich möchte einen Quiz über die Geschichte",
            "Bitte korrigieren Sie: 'Ich hat einen Buch gelesen'",
            "Auf Wiedersehen!"
        ]
        
        print("=" * 60)
        print("LANGUAGE LEARNING AGENT SYSTEM")
        print("=" * 60)
        
        for i, user_input in enumerate(workflow, 1):
            print(f"\n[USER INPUT {i}]: {user_input}")
            print("-" * 60)
            
            response = await system.process_user_input(user_input)
            
            print(f"[AGENT]: {response['agent']}")
            print(f"[SUCCESS]: {response['success']}")
            if response['success']:
                print(f"[RESPONSE]: {response['data']}")
            else:
                print(f"[ERROR]: {response['error']}")
            
            print("-" * 60)
    
    asyncio.run(main())
