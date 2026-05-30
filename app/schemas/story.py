from pydantic import BaseModel


class Story(BaseModel):
    id: int
    title: str
    content: str
    level: str
    theme: str

