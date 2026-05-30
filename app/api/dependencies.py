from app.agents.storyteller import StoryTellerAgent
from app.core.config import settings

# This allows you to swap the real agent for a 
# "MockAgent" easily during testing.
def get_story_agent() -> StoryTellerAgent:
    return StoryTellerAgent() 