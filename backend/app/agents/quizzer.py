from typing import Any, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import Agent, load_agent_prompt


class QuizzerAgent(Agent):
    """
    The QuizzerAgent creates and evaluates quizzes based on story content.
    
    Responsibilities:
    - Generate comprehension questions about stories
    - Create vocabulary quizzes from story content
    - Evaluate user answers and provide feedback
    - Track learning progress
    
    Quiz types:
    - Multiple choice
    - Short answer
    - Fill-in-the-blank
    - Vocabulary
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model=model)
        self.quiz_prompt = ChatPromptTemplate.from_messages([
            ("system", load_agent_prompt("quiz_prompt")),
            ("human", "Create a quiz for this story:\n\n{story_content}\n\nLevel: {level}")
        ])

    async def run(
        self,
        story_content: str,
        level: str,
        question_count: int = 5,
        quiz_type: str = "multiple_choice"
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on story content.
        
        Args:
            story_content: The story text to base quiz on
            level: Language level (A1, A2, B1, B2, C1, C2)
            question_count: Number of questions to generate
            quiz_type: Type of quiz (multiple_choice, short_answer, fill_blank)
            
        Returns:
            Dict with quiz questions and answer key
        """
        try:
            if not await self.validate_input(
                story_content=story_content,
                level=level
            ):
                return self._format_response(False, error="Invalid input parameters")
            
            chain = self.quiz_prompt | self.llm
            response = await chain.ainvoke({
                "story_content": story_content,
                "level": level,
                "question_count": question_count,
                "quiz_type": quiz_type
            })
            
            return self._format_response(
                success=True,
                data={
                    "quiz": response.content,
                    "level": level,
                    "quiz_type": quiz_type,
                    "question_count": question_count
                }
            )
            
        except Exception as e:
            return self._format_response(
                success=False,
                error=f"Error generating quiz: {str(e)}"
            )

    async def validate_input(self, story_content: str, level: str, **kwargs) -> bool:
        """Validate story content and level."""
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if not story_content or len(story_content.strip()) < 50:
            return False
        if level not in valid_levels:
            return False
        return True

    async def evaluate_answer(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        level: str
    ) -> Dict[str, Any]:
        """
        Evaluate a user's answer to a quiz question.
        
        Args:
            question: The quiz question
            user_answer: User's provided answer
            correct_answer: The correct answer
            level: User's language level for feedback depth
            
        Returns:
            Dict with evaluation result and feedback
        """
        try:
            eval_prompt = ChatPromptTemplate.from_messages([
                ("system", load_agent_prompt("quiz_evaluation")),
                ("human", """Question: {question}
                            
                            Student's answer: {user_answer}
                            
                            Correct answer: {correct_answer}""")
            ])
            
            chain = eval_prompt | self.llm
            response = await chain.ainvoke({
                "question": question,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "level": level
            })
            
            return self._format_response(
                success=True,
                data={
                    "question": question,
                    "user_answer": user_answer,
                    "feedback": response.content
                }
            )
            
        except Exception as e:
            return self._format_response(
                success=False,
                error=f"Error evaluating answer: {str(e)}"
            )