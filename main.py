"""FastAPI server for Deep Research Agent."""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json

from langchain_core.messages import HumanMessage
from agent.agent_workflow import DeepResearchWorkflow

app = FastAPI(title="Deep Research Agent")


class Config(BaseModel):
    num_searches: int = 3
    max_iterations: int = 2
    results_per_search: int = 3


class Request(BaseModel):
    query: str
    history: List[Dict[str, str]] = []
    config: Optional[Config] = None
    provider: Optional[str] = None
    report_style: Optional[str] = None


@app.post("/research/stream")
async def research_stream(req: Request):
    """Stream research progress and final report."""

    # Build config override
    override = {}
    if req.config:
        override = {
            "research.num_searches": req.config.num_searches,
            "research.max_iterations": req.config.max_iterations,
            "research.results_per_search": req.config.results_per_search,
        }
    if req.provider:
        override["llm.provider"] = req.provider
    if req.report_style:
        override["report.style"] = req.report_style

    # Build initial state with messages
    messages = [HumanMessage(content=m["content"]) for m in req.history[-6:] if m["role"] == "user"]
    messages.append(HumanMessage(content=req.query))

    state = {
        "messages": messages,
        "original_query": req.query,
        "iteration": 0,
        "gathered_info": [],
    }

    def generate():
        try:
            workflow = DeepResearchWorkflow(config_override=override)
            for event in workflow.graph.stream(state, {"configurable": {"thread_id": "default"}}):
                for node, output in event.items():
                    for msg in output.get("messages", []):
                        yield json.dumps({"node": node, "type": msg.type, "content": msg.content}) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
