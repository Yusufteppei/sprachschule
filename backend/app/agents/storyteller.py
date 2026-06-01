from typing import Any, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.story import Story
from app.agents.base import Agent, load_agent_prompt


class StorytellerAgent(Agent):
    """
    The StorytellerAgent generates stories for language learning.
    
    It creates contextually appropriate stories based on:
    - User's language level (A1, A2, B1, B2, C1, C2)
    - Chosen theme/topic
    - User's learning history and preferences
    
    Tools:
    - Generates original stories with vocabulary suited to the level
    - Optionally searches database for relevant pre-made stories
    """
    
    def __init__(self, model: str = "gpt-4o"):
        super().__init__(model=model)
        self.story_prompt = ChatPromptTemplate.from_messages([
            ("system", load_agent_prompt("storyteller")),
            ("human", "Create a {level} level story in {language} about: {theme}")
        ])
        self.title_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You create short, natural titles for language-learning stories. "
                "Return only the title, with no labels, quotes, or explanation."
            ),
            (
                "human",
                "Create a concise title in {language} for this story:\n\n{story_content}"
            )
        ])
    
    async def run(
        self,
        level: str,
        theme: str = "Technology",
        language: str = "German",
        story_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a story for the user.
        
        Args:
            level: Language level (A1, A2, B1, B2, C1, C2)
            theme: Story topic/theme
            language: Target language for the story
            story_id: Optional ID if retrieving from database
            
        Returns:
            Dict with story data and metadata
        """
        try:
            if not await self.validate_input(level=level, theme=theme, language=language):
                return self._format_response(False, error="Invalid input parameters")
            
            # Generate story using LLM
            chain = self.story_prompt | self.llm
            response = await chain.ainvoke({
                "level": level,
                "theme": theme,
                "language": language,
            })
            
            story_content = response.content
            title = await self._generate_title(
                story_content=story_content,
                language=language,
            )
            
            # Create Story object
            story = Story(
                id=story_id or 1,
                title=title,
                content=story_content,
                level=level,
                theme=theme
            )
            
            return self._format_response(
                success=True,
                data={
                    "story": story.model_dump(),
                    "language": language,
                }
            )
            
        except Exception as e:
            return self._format_response(
                success=False,
                error=f"Error generating story: {str(e)}"
            )
    
    async def validate_input(self, level: str, theme: str, language: str, **kwargs) -> bool:
        """Validate language level, theme, and target language."""
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if level not in valid_levels:
            return False
        if not theme or len(theme.strip()) == 0:
            return False
        if not language or len(language.strip()) == 0:
            return False
        return True

    async def _generate_title(self, story_content: str, language: str) -> str:
        """Generate a title from the actual story content."""
        try:
            chain = self.title_prompt | self.llm
            response = await chain.ainvoke({
                "story_content": story_content,
                "language": language,
            })
            title = self._clean_title(response.content)
            if title:
                return title
        except Exception:
            pass

        return self._fallback_title(story_content)

    def _clean_title(self, title: str) -> str:
        title = (title or "").strip()
        for prefix in ("Title:", "Titre:", "Titel:", "Título:", "Titolo:"):
            if title.lower().startswith(prefix.lower()):
                title = title[len(prefix):].strip()

        return title.strip(" \t\r\n\"'“”‘’")

    def _fallback_title(self, story_content: str) -> str:
        first_line = next(
            (line.strip() for line in story_content.splitlines() if line.strip()),
            ""
        )
        if not first_line:
            return "Untitled Story"

        words = first_line.strip(" \t\r\n\"'“”‘’").split()
        return " ".join(words[:8]).rstrip(".,;:!?")


class MockStoryteller(StorytellerAgent):
    """Mock storyteller for testing without LLM calls."""
    
    async def run(
        self,
        level: str,
        theme: str = "Technology",
        language: str = "German",
        story_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Return a mock story for testing."""
        content = (
            f"[Mock] Once upon a time in a {language}-speaking world, there was "
            f"a curious learner who discovered something surprising about {theme}..."
        )
        story = Story(
            id=story_id or 1,
            title=self._fallback_title(content),
            content=content,
            level=level,
            theme=theme
        )
        
        return self._format_response(
            success=True,
            data={
                "story": story.model_dump(),
                "language": language,
            }
        )
