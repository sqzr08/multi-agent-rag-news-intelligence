"""
LangGraph pipeline — wires all agents into a StateGraph.
"""

from datetime import date
from langgraph.graph import StateGraph, END

from graph.state import PipelineState
from agents.retriever import retriever_node
from agents.analyzer import analyzer_node
from agents.insights import insights_node
from agents.report_writer import report_writer_node


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    # Register nodes
    graph.add_node("retriever", retriever_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("insights", insights_node)
    graph.add_node("report_writer", report_writer_node)

    # Define edges 
    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "analyzer")
    graph.add_edge("analyzer", "insights")
    graph.add_edge("insights", "report_writer")
    graph.add_edge("report_writer", END)

    return graph.compile()


async def run_pipeline(query: str = "Artificial Intelligence") -> PipelineState:
    """Entry point — initialise state and run the full graph."""
    initial_state: PipelineState = {
        "query": query,
        "run_date": date.today().isoformat(),
        "raw_articles": [],
        "analyzed_articles": [],
        "insights": None,
        "report_markdown": None,
        "report_path": None,
        "errors": [],
    }

    app = build_graph()
    final_state = await app.ainvoke(initial_state)

    if final_state.get("report_path"):
        print(f"\n✅ Report saved to: {final_state['report_path']}")
    if final_state.get("errors"):
        print(f"\n⚠️  Errors encountered: {final_state['errors']}")

    return final_state
