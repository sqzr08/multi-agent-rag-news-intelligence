"""
Insights Agent
──────────────
Synthesizes today's analyzed articles into themes, emerging topics,
key entities, and an executive summary — using Gemini with structured output.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

import config
from graph.state import PipelineState, AnalyzedArticle, InsightsOutput

_base_llm = ChatGoogleGenerativeAI(
    model=config.GEMINI_MODEL,
    google_api_key=config.GEMINI_API_KEY,
    temperature=0.3,
)

llm = _base_llm.with_structured_output(InsightsOutput)

SYSTEM_PROMPT = """You are a senior AI industry analyst writing a daily intelligence briefing.
Given a set of today's AI news articles, identify:
- The core themes running across the articles
- Topics that appear to be gaining momentum
- The most prominent organizations, people, or products
- A concise executive summary for a senior audience

Be specific and avoid generic statements. Focus on what is actually notable today.
"""


def format_articles(articles: list[AnalyzedArticle]) -> str:
    lines = []
    for a in sorted(articles, key=lambda x: x.importance_score, reverse=True):
        lines.append(
            f"[{a.date}] {a.title} ({a.source})\n"
            f"  Topics: {', '.join(a.topics)}\n"
            f"  Entities: {', '.join(a.entities)}\n"
            f"  Sentiment: {a.sentiment.value}  |  Importance: {a.importance_score:.2f}\n"
            f"  Summary: {a.summary}\n"
        )
    return "\n".join(lines)


# Insights LangGraph Node

async def insights_node(state: PipelineState) -> PipelineState:
    print(f"\n [Insights] Synthesizing insights from {len(state['analyzed_articles'])} articles...")

    today_articles = state["analyzed_articles"]
    if not today_articles:
        state["errors"].append("No analyzed articles to generate insights from.")
        return state

    prompt = (
        f"Today's date: {state['run_date']}\n"
        f"Query: {state['query']}\n\n"
        f"## Today's Articles\n\n"
        f"{format_articles(today_articles)}"
    )

    try:
        insights: InsightsOutput = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        state["insights"] = insights
        print(
            f"   ✅ {len(insights.todays_themes)} themes, "
            f"{len(insights.emerging_topics)} emerging topics"
        )
    except Exception as e:
        state["errors"].append(f"Insights LLM error: {e}")
        state["insights"] = InsightsOutput(
            todays_themes=[],
            emerging_topics=[],
            key_entities_today=[],
            executive_summary="Insights generation failed.",
        )

    return state
