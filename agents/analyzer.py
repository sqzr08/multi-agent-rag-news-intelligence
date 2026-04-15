"""
Analyzer Agent
──────────────
For each scraped article:
  1. Use Gemini with structured output to extract
     topics, entities, sentiment, importance score, and summary.
  2. Pydantic model ArticleAnalysis enforces the LLM output schema and provides type safety.
"""

import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

import config
from graph.state import (
    PipelineState,
    RawArticle,
    ArticleAnalysis,
    AnalyzedArticle,
    Sentiment,
)

_base_llm = ChatGoogleGenerativeAI(
    model=config.GEMINI_MODEL,
    google_api_key=config.GEMINI_API_KEY,
    temperature=0.2,
)

llm = _base_llm.with_structured_output(ArticleAnalysis)

SYSTEM_PROMPT = """You are an AI news analyst. Analyze the given article and return
structured data according to the required schema.

Scoring guide for importance_score:
- 0.8–1.0: Major breakthrough, funding >$100M, regulatory change, major product launch
- 0.5–0.8: Notable research, mid-size company news, product updates
- 0.0–0.5: Opinion pieces, minor updates, speculation
"""


# Article analysis function that calls Gemini and returns a validated ArticleAnalysis model.

async def analyze_article(article: RawArticle) -> ArticleAnalysis:
    """
    Call Gemini and return a validated ArticleAnalysis.
    Falls back to a safe default if the LLM call fails.
    """
    prompt = (
        f"Title: {article.title}\n"
        f"Source: {article.source}\n"
        f"Date: {article.date}\n\n"
        f"Article text:\n{article.raw_text[:4000]}"
    )

    try:
        result: ArticleAnalysis = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return result
    except Exception as e:
        return ArticleAnalysis(
            summary=article.raw_text[:300],
            topics=[],
            entities=[],
            sentiment=Sentiment.neutral,
            importance_score=0.3,
        )


# Analyzer LangGraph Node

async def analyzer_node(state: PipelineState) -> PipelineState:
    print(f"\n [Analyzer] Analyzing {len(state['raw_articles'])} articles...")

    analyzed: list[AnalyzedArticle] = []
    articles = state["raw_articles"]

    batch_size = 5
    for i in range(0, len(articles), batch_size):
        batch = articles[i : i + batch_size]
        tasks = [analyze_article(a) for a in batch]
        results: list[ArticleAnalysis] = await asyncio.gather(*tasks)

        for article, analysis in zip(batch, results):
            analyzed.append(
                AnalyzedArticle(
                    url=article.url,
                    title=article.title,
                    source=article.source,
                    date=article.date,
                    summary=analysis.summary,
                    topics=analysis.topics,
                    entities=analysis.entities,
                    sentiment=analysis.sentiment,
                    importance_score=analysis.importance_score,
                    raw_text=article.raw_text,
                )
            )

        print(f"   Processed {min(i + batch_size, len(articles))}/{len(articles)}")

    state["analyzed_articles"] = analyzed
    print(f"   ✅ Analyzed {len(analyzed)} articles")
    return state
