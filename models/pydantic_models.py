from typing import Annotated, List, TypedDict
import operator
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

class SearchQuery(BaseModel):
    query: str = Field(description="The specific search query to execute")
    rationale: str = Field(description="Why this query is necessary")

class ResearchPlan(BaseModel):
    queries: List[SearchQuery]
    reflection: str = Field(description="Reasoning behind the research strategy")

class SearchResultItem(BaseModel):
    url: str
    title: str
    content: str
    source_id: int

class CritiqueResponse(BaseModel):
    is_sufficient: bool = Field(description="True if enough info is gathered")
    feedback: str = Field(description="What information is missing, if any")

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        # Handle LLM returning "True"/"False" strings instead of booleans
        if isinstance(obj, dict) and "is_sufficient" in obj:
            val = obj["is_sufficient"]
            if isinstance(val, str):
                obj["is_sufficient"] = val.lower() == "true"
        return super().model_validate(obj, *args, **kwargs)

class ResearchState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]  # Required by spec
    original_query: str
    plan: List[SearchQuery]
    gathered_info: Annotated[List[SearchResultItem], operator.add]
    critique_feedback: str
    final_report: str
    iteration: int
