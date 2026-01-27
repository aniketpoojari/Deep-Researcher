"""Generate a PNG image of the LangGraph workflow.

Usage:
    python -m evals.generate_graph
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from agent.agent_workflow import DeepResearchWorkflow

workflow = DeepResearchWorkflow()
graph_png = workflow.graph.get_graph().draw_mermaid_png()

output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graph.png")
with open(output_path, "wb") as f:
    f.write(graph_png)

print(f"Graph saved to {output_path}")
