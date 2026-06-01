from enum import Enum


class TargetLanguage(str, Enum):
    """Available languages for learning"""
    FRENCH = "French"
    SPANISH = "Spanish"
    ITALIAN = "Italian"
    GERMAN = "German"
    #PORTUGUESE = "Portuguese"
    #DUTCH = "Dutch"
    RUSSIAN = "Russian"
    JAPANESE = "Japanese"
    MANDARIN = "Mandarin"


class ProficiencyLevel(str, Enum):
    """CEFR Language Proficiency Levels"""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


