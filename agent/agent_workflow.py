"""LangGraph workflow for deep research with iterative refinement."""

from langgraph.graph import StateGraph, END, START
from langgraph.constants import Send
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from models.pydantic_models import ResearchState, ResearchPlan, CritiqueResponse, SearchResultItem, SearchQuery
from prompt_library.prompt import PLANNER_PROMPT, CRITIQUE_PROMPT, WRITER_PROMPTS
from utils.model_loader import ModelLoader
from utils.config_loader import ConfigLoader
from tools.web_search_tool import WebSearchTool
from logger.logging import get_logger

logger = get_logger(__name__)


class DeepResearchWorkflow:
    """
    Research workflow: Planner -> Researcher (parallel) -> Critique -> Writer
                       ^__________________________|  (if insufficient)
    """

    def __init__(self, config_override: dict = None):
        self._config = ConfigLoader()
        self._override = config_override or {}
        self.llm = ModelLoader(self._cfg("llm.provider", "groq")).load()
        self._search = WebSearchTool().tools[0]
        self.graph = self._build()

    def _cfg(self, key, default=None):
        return self._override.get(key, self._config.get(key, default))

    def _build(self):
        g = StateGraph(ResearchState)
        g.add_node("planner", self._plan)
        g.add_node("researcher", self._research)
        g.add_node("critique", self._critique)
        g.add_node("writer", self._write)

        g.add_edge(START, "planner")
        g.add_conditional_edges("planner", lambda s: [Send("researcher", {"q": q.query}) for q in s["plan"]], ["researcher"])
        g.add_edge("researcher", "critique")
        g.add_conditional_edges("critique", self._check, {"continue": "planner", "finish": "writer"})
        g.add_edge("writer", END)

        return g.compile(checkpointer=MemorySaver())

    def _plan(self, state: ResearchState):
        logger.info("=== PLANNER ===")
        history = "\n".join(f"{m.type}: {m.content[:200]}" for m in (state.get("messages") or [])[-4:]) or "None"

        prompt = PLANNER_PROMPT.format(
            query=state["original_query"],
            feedback=state.get("critique_feedback", ""),
            max_queries=self._cfg("research.num_searches", 3),
            chat_history=history
        )

        try:
            plan = self.llm.with_structured_output(ResearchPlan).invoke([HumanMessage(content=prompt)])
            return {
                "plan": plan.queries,
                "iteration": state.get("iteration", 0) + 1,
                "messages": [AIMessage(content=f"**Plan:**\n" + "\n".join(f"- {q.query}" for q in plan.queries))]
            }
        except Exception as e:
            logger.error(f"Plan failed: {e}")
            return {
                "plan": [SearchQuery(query=state["original_query"], rationale="fallback")],
                "iteration": state.get("iteration", 0) + 1,
                "messages": [AIMessage(content=f"Fallback: {state['original_query']}")]
            }

    def _research(self, state: dict):
        q = state["q"]
        logger.info(f"=== RESEARCH: {q[:40]} ===")

        try:
            res = self._search.invoke({"query": q, "max_results": self._cfg("research.results_per_search", 3)})
            if not res.get("success"):
                raise Exception(res.get("error"))

            items = [SearchResultItem(source_id=abs(hash(r["url"])) % 10000, url=r["url"], title=r["title"], content=r.get("snippet", "")) for r in res["results"]]
            return {
                "gathered_info": items,
                "messages": [ToolMessage(content=f"**Search:** {q}\n" + "\n".join(f"[{i.source_id}] {i.title}" for i in items), tool_call_id=f"s{abs(hash(q))%1000}")]
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"gathered_info": [], "messages": [ToolMessage(content=f"Search failed: {q}", tool_call_id=f"s{abs(hash(q))%1000}")]}

    def _critique(self, state: ResearchState):
        logger.info("=== CRITIQUE ===")
        info = state.get("gathered_info", [])
        if not info:
            return {"critique_feedback": "No results", "messages": [AIMessage(content="**Critique:** No results")]}

        context = "\n".join(f"[{i.source_id}] {i.title}: {i.content}" for i in info)
        prompt = CRITIQUE_PROMPT.format(query=state["original_query"], context=context)

        try:
            # Use json_mode to avoid strict type validation issues with Groq
            r = self.llm.with_structured_output(CritiqueResponse, method="json_mode").invoke([
                HumanMessage(content=prompt + "\n\nRespond in JSON: {\"is_sufficient\": true or false, \"feedback\": \"...\"}")
            ])
            # Handle string booleans from LLM
            is_suff = r.is_sufficient if isinstance(r.is_sufficient, bool) else str(r.is_sufficient).lower() == "true"
            fb = "Sufficient" if is_suff else r.feedback
            return {"critique_feedback": fb, "messages": [AIMessage(content=f"**Critique:** {fb}")]}
        except Exception as e:
            logger.error(f"Critique failed: {e}")
            return {"critique_feedback": "Sufficient", "messages": [AIMessage(content="**Critique:** Skipped")]}

    def _check(self, state: ResearchState):
        if state["critique_feedback"] == "Sufficient" or state["iteration"] >= self._cfg("research.max_iterations", 2):
            return "finish"
        return "continue"

    def _write(self, state: ResearchState):
        logger.info("=== WRITER ===")
        info = state.get("gathered_info", [])
        if not info:
            return {"final_report": "No data found.", "messages": [AIMessage(content="No data found.")]}

        context = "\n".join(f"[{i.source_id}] {i.title}\nURL: {i.url}\n{i.content}\n" for i in info)
        style = self._cfg("report.style", "detailed")
        writer_template = WRITER_PROMPTS.get(style, WRITER_PROMPTS["detailed"])
        prompt = writer_template.format(query=state["original_query"], context=context)

        try:
            r = self.llm.invoke([HumanMessage(content=prompt)])
            return {"final_report": r.content, "messages": [AIMessage(content=r.content)]}
        except Exception as e:
            return {"final_report": f"Error: {e}", "messages": [AIMessage(content=f"Error: {e}")]}
