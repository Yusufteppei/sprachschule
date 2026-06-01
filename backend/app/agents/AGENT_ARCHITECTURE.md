# Agent Architecture - Object-Oriented Design

## Overview

The language learning system uses an **Object-Oriented Architecture** where each agent is a specialized class that inherits from a common `Agent` base class. This design ensures:

- **Single Responsibility**: Each agent handles one specific domain
- **Code Reuse**: Common functionality in the base class
- **Easy Extension**: New agents can be added by extending the base class
- **Clear Contracts**: Standard interface for all agents

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│         USER (Text/Speech Input)        │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼────────┐
         │ ModeratorAgent │ ◄─── ONLY agent that communicates with user
         │  (Coordinator) │
         └───────┬────────┘
                 │
         ┌───────┴─────────────────────┐
         │                             │
    ┌────▼──────┐  ┌──────────┐  ┌────▼──────┐
    │ Storyteller│  │Grammarian│  │  Quizzer  │
    │  Agent    │  │  Agent   │  │  Agent    │
    └───────────┘  └──────────┘  └───────────┘
```

## Class Hierarchy

### Base Class: `Agent` (base.py)

All agents inherit from the abstract `Agent` class:

```python
class Agent(ABC):
    def __init__(self, model: str = "gpt-4o-mini", language: str = "de"):
        self.llm = ChatOpenAI(model=model)
        self.language = language
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the agent's task"""
        pass
```

**Common Methods:**
- `run()` - Abstract method, implemented by each subclass
- `validate_input()` - Validate input parameters
- `_format_response()` - Standard response format

### Specialized Agents

#### 1. **StorytellerAgent** (storyteller.py)

Generates stories for language learning.

**Key Methods:**
- `run(level, theme)` - Generate a story
- `validate_input()` - Ensure valid level (A1-C2) and theme

**Usage:**
```python
storyteller = StorytellerAgent()
result = await storyteller.run(level="B1", theme="Technology")
# Returns: {"success": True, "data": {"story": Story(...) }}
```

**Responsibilities:**
- Create contextually appropriate stories
- Match vocabulary to language level
- Ensure educational but engaging content

#### 2. **GrammarianAgent** (grammarian.py)

Corrects grammar and explains German grammar rules.

**Key Methods:**
- `run(text, language_level)` - Analyze text for grammar errors
- `explain_rule(rule, example)` - Explain specific grammar rules
- `validate_input()` - Ensure valid text input

**Usage:**
```python
grammarian = GrammarianAgent()
result = await grammarian.run(text="Ich hat ein Buch gelesen", language_level="B1")
# Returns: {"success": True, "data": {"analysis": "...explanation..." }}
```

**Responsibilities:**
- Identify grammar errors
- Provide corrections
- Explain rules in learner-friendly language
- Focus on cases, verb conjugation, word order

#### 3. **QuizzerAgent** (quizzer.py)

Creates quizzes based on story content and evaluates answers.

**Key Methods:**
- `run(story_content, level, question_count)` - Generate quiz
- `evaluate_answer(question, user_answer, correct_answer)` - Grade answer
- `validate_input()` - Ensure valid story and level

**Usage:**
```python
quizzer = QuizzerAgent()
result = await quizzer.run(story_content="...", level="B1", question_count=5)
# Returns: {"success": True, "data": {"quiz": "...questions..." }}
```

**Responsibilities:**
- Generate comprehension questions
- Create vocabulary quizzes
- Evaluate user answers
- Provide constructive feedback

#### 4. **ModeratorAgent** (moderator.py)

The coordinator that interfaces with users.

**Key Methods:**
- `run(user_input)` - Main entry point for user interaction
- `_route_request()` - Decide which agent to use
- `_extract_*_params()` - Parse parameters for each agent

**Usage:**
```python
moderator = ModeratorAgent()
result = await moderator.run("Tell me a B1 story about nature")
# Moderator automatically routes to storyteller and returns formatted response
```

**Responsibilities:**
- Accept user input (text/speech)
- Route requests to appropriate agents
- Coordinate agent responses
- Present results to user
- **ONLY** agent that communicates directly with user

## Response Format

All agents return a standardized response format:

```python
{
    "success": bool,           # Whether operation succeeded
    "agent": str,              # Name of agent that processed request
    "data": dict | None,       # Result data (if successful)
    "error": str | None        # Error message (if failed)
}
```

### Example Responses

**Story Generation:**
```python
{
    "success": True,
    "agent": "StorytellerAgent",
    "data": {
        "story": {
            "id": 1,
            "title": "A B1 story about Technology",
            "content": "...",
            "level": "B1",
            "theme": "Technology"
        }
    },
    "error": None
}
```

**Grammar Correction:**
```python
{
    "success": True,
    "agent": "GrammarianAgent",
    "data": {
        "original_text": "Ich hat ein Buch gelesen",
        "analysis": "ERRORS: 'hat' is wrong conjugation...\nCORRECTION: Ich habe ein Buch gelesen\nEXPLANATION: ...",
        "level": "B1"
    },
    "error": None
}
```

## Workflow Example

### User Journey: Story Learning Session

```
1. USER INPUT: "Erzählen Sie mir eine B1-Geschichte über Technologie"
   ↓
2. ModeratorAgent routes to StorytellerAgent
   ↓
3. StorytellerAgent generates story
   ↓
4. ModeratorAgent formats and presents story to user
   ↓
5. USER INPUT: "Ich möchte einen Quiz"
   ↓
6. ModeratorAgent routes to QuizzerAgent
   ↓
7. QuizzerAgent generates comprehension questions
   ↓
8. ModeratorAgent presents quiz to user
   ↓
9. USER ANSWERS: Quiz responses
   ↓
10. ModeratorAgent routes to QuizzerAgent for evaluation
    ↓
11. QuizzerAgent evaluates and provides feedback
    ↓
12. ModeratorAgent presents feedback to user
```

## Design Principles

### 1. **Single Responsibility**
- Each agent has ONE job
- Storyteller only generates stories
- Grammarian only handles grammar
- Moderator only interfaces with user

### 2. **Open/Closed Principle**
- Open for extension (add new agents by extending `Agent`)
- Closed for modification (base class doesn't change)

### 3. **Dependency Inversion**
- All agents depend on abstract `Agent` base class
- Moderator doesn't need to know implementation details

### 4. **Interface Segregation**
- Each agent has only the methods it needs
- Users interact via standard `run()` method

### 5. **Composition over Inheritance**
- ModeratorAgent composes instances of other agents
- Agents don't inherit from each other (only from base)

## Adding New Agents

To add a new agent (e.g., `SpeechCoachAgent`):

```python
# 1. Create new file: speech_coach.py

from app.agents.base import Agent
from typing import Any, Dict

class SpeechCoachAgent(Agent):
    """Handles pronunciation and accent coaching."""
    
    async def run(self, audio_file: str, level: str) -> Dict[str, Any]:
        try:
            if not await self.validate_input(audio_file=audio_file, level=level):
                return self._format_response(False, error="Invalid input")
            
            # Your implementation here
            
            return self._format_response(True, data={"feedback": "..."})
        except Exception as e:
            return self._format_response(False, error=str(e))
    
    async def validate_input(self, audio_file: str, level: str, **kwargs) -> bool:
        return bool(audio_file and level in ["A1", "A2", "B1", "B2", "C1", "C2"])

# 2. Update ModeratorAgent to route to it
# Add to agents/moderator.py:
# - Import SpeechCoachAgent
# - Add instance in __init__
# - Add routing logic in _route_request()
```

## Testing

Use the `MockStoryteller` for testing without LLM calls:

```python
from app.agents.main import LanguageLearningSystem

async def test_workflow():
    system = LanguageLearningSystem(use_mock_storyteller=True)
    
    result = await system.process_user_input("Story about cats")
    assert result["success"] is True
    assert "Mock" in result["data"]["content"]
```

## Configuration

### Model Selection

Change which LLM model each agent uses:

```python
# Use gpt-4 for better quality
storyteller = StorytellerAgent(model="gpt-4")

# Use gpt-4o-mini for faster, cheaper responses
grammarian = GrammarianAgent(model="gpt-4o-mini")
```

### Language Support

Currently configured for German (de). Can extend:

```python
agent = StorytellerAgent(language="de")  # German
agent = StorytellerAgent(language="es")  # Spanish
agent = StorytellerAgent(language="fr")  # French
```

## Error Handling

All agents handle errors gracefully:

```python
{
    "success": False,
    "agent": "StorytellerAgent",
    "data": None,
    "error": "Error generating story: API rate limit exceeded"
}
```

Moderator intercepts these errors and can:
- Return error message to user
- Retry with different agent
- Provide fallback response

## Future Enhancements

1. **Speech Coach Agent** - Pronunciation feedback
2. **Vocabulary Agent** - Vocabulary learning and spaced repetition
3. **Writing Coach Agent** - Paragraph and essay feedback
4. **Conversation Agent** - Practice speaking with AI
5. **Progress Tracker** - Monitor learning progress across sessions
6. **Content Database** - Persist and retrieve user stories

## File Structure

```
backend/app/agents/
├── base.py              # Abstract Agent base class
├── moderator.py         # ModeratorAgent (coordinator)
├── storyteller.py       # StorytellerAgent
├── grammarian.py        # GrammarianAgent
├── quizzer.py           # QuizzerAgent
├── main.py              # System entry point & examples
└── prompts/
    └── storyteller.txt  # Prompts for storyteller
```
