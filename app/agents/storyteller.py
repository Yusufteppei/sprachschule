class StoryTellerAgent:
    """
        The StoryTellerAgent is responsible for generating the story based
        on the user's settings and past interactions, e.g fixed grammar and
        word pronunciations.
    """
    async def run(self, level:str, theme:str = "Software Development"):
        
        return {
            "text": f"Once upon a time in the world of {theme}, there was a {level} developer who loved to code.",
            "level": level,
            "theme": theme
        }