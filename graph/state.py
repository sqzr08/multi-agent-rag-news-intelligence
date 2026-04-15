"""
Shared LangGraph state — typed dict passed between all agents.
"""

from typing import TypedDict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


# Enums 

class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


# Pydantic models

class RawArticle(BaseModel):
    """Output of the Retriever Agent."""
    url: str
    title: str
    source: str
    date: str                  # ISO format: YYYY-MM-DD
    raw_text: str
    url_hash: str              # sha256 of URL for deduplication


class ArticleAnalysis(BaseModel):
    """Structured LLM output from the Analyzer Agent (enforced by Pydantic)."""
    summary: str = Field(description="2-3 sentence factual summary of the article")
    topics: List[str] = Field(description="List of AI topics covered, e.g. LLM, agents, robotics")
    entities: List[str] = Field(description="Named organizations, people, or products mentioned")
    sentiment: Sentiment = Field(description="Overall sentiment of the article")
    importance_score: float = Field(
        ge=0.0, le=1.0,
        description="Importance score from 0.0 (low) to 1.0 (high)"
    )


class AnalyzedArticle(BaseModel):
    """Article metadata + LLM analysis, passed to downstream agents."""
    url: str
    title: str
    source: str
    date: str
    summary: str
    topics: List[str]
    entities: List[str]
    sentiment: Sentiment
    importance_score: float
    raw_text: str


class InsightsOutput(BaseModel):
    """Full output of the Insights Agent."""
    todays_themes: List[str] = Field(description="Core themes from today's articles")
    emerging_topics: List[str] = Field(description="Topics gaining momentum today")
    key_entities_today: List[str] = Field(description="Most prominent orgs/people/products today")
    executive_summary: str = Field(description="3-5 sentence briefing for senior readers")


# LangGraph pipeline state 

class PipelineState(TypedDict):
    """Typed dict shared across all LangGraph nodes."""
    query: str
    run_date: str                              # YYYY-MM-DD
    raw_articles: List[RawArticle]
    analyzed_articles: List[AnalyzedArticle]
    insights: Optional[InsightsOutput]
    report_markdown: Optional[str]
    report_path: Optional[str]
    errors: List[str]
