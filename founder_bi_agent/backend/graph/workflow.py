from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.graph.nodes import FounderBINodes
from founder_bi_agent.backend.graph.state import BIState


def _after_clarifier(state: dict[str, Any]) -> str:
    return "ask_user" if state.get("needs_clarification") else "continue"

def _after_executive_planner(state: dict[str, Any]) -> str:
    return "search" if state.get("needs_web_search") else "skip"

def _after_sql_guardrail(state: dict[str, Any]) -> str:
    return "blocked" if state.get("sql_validation_error") else "go"


def build_graph(settings: AgentSettings):
    nodes = FounderBINodes(settings)
    graph = StateGraph(BIState)

    graph.add_node("intent_router", nodes.intent_router)
    graph.add_node("clarifier", nodes.clarifier)
    graph.add_node("deepseek_executive_planner", nodes.deepseek_executive_planner)
    graph.add_node("web_researcher", nodes.web_researcher)
    graph.add_node("schema_discovery", nodes.schema_discovery)
    graph.add_node("data_fetch_live", nodes.data_fetch_live)
    graph.add_node("normalize_data", nodes.normalize_data)
    graph.add_node("quality_profiler", nodes.quality_profiler)
    graph.add_node("text2sql_planner", nodes.text2sql_planner)
    graph.add_node("sql_guardrail", nodes.sql_guardrail)
    graph.add_node("sql_execute", nodes.sql_execute)
    graph.add_node("insight_writer", nodes.insight_writer)
    graph.add_node("viz_builder", nodes.viz_builder)
    graph.add_node("reflection_judge", nodes.reflection_judge)

    graph.add_edge(START, "intent_router")
    graph.add_edge("intent_router", "clarifier")
    graph.add_conditional_edges(
        "clarifier",
        _after_clarifier,
        {
            "ask_user": END,
            "continue": "deepseek_executive_planner",
        },
    )
    
    graph.add_conditional_edges(
        "deepseek_executive_planner",
        _after_executive_planner,
        {
            "search": "web_researcher",
            "skip": "schema_discovery",
        },
    )
    graph.add_edge("web_researcher", "schema_discovery")
    
    graph.add_edge("schema_discovery", "data_fetch_live")
    graph.add_edge("data_fetch_live", "normalize_data")
    graph.add_edge("normalize_data", "quality_profiler")
    graph.add_edge("quality_profiler", "text2sql_planner")
    graph.add_edge("text2sql_planner", "sql_guardrail")
    graph.add_conditional_edges(
        "sql_guardrail",
        _after_sql_guardrail,
        {
            "blocked": END,
            "go": "sql_execute",
        },
    )
    graph.add_edge("sql_execute", "insight_writer")
    graph.add_edge("insight_writer", "viz_builder")
    graph.add_edge("viz_builder", "reflection_judge")
    graph.add_edge("reflection_judge", END)

    return graph.compile()
