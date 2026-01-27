"""Run LangSmith evaluations for the Deep Research Agent.

Usage:
    python -m evals.run_evals

This script:
1. Creates a dataset in LangSmith (if it doesn't exist)
2. Runs the research workflow against each example
3. Evaluates outputs using custom evaluators
4. Results are visible in LangSmith Studio
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langsmith import Client
from langsmith.evaluation import evaluate

from langchain_core.messages import HumanMessage
from agent.agent_workflow import DeepResearchWorkflow
from evals.evaluators import has_citations, report_length, has_markdown_headers, no_errors

client = Client()

# --- Dataset ---
DATASET_NAME = "deep-researcher-evals"

EXAMPLES = [
    {
        "query": "What are the main benefits of solar energy?",
    },
    {
        "query": "How does the Python GIL work?",
    },
    {
        "query": "What is retrieval augmented generation (RAG)?",
    },
]


def create_dataset():
    """Create or fetch the evaluation dataset in LangSmith."""
    datasets = list(client.list_datasets(dataset_name=DATASET_NAME))
    if datasets:
        print(f"Dataset '{DATASET_NAME}' already exists.")
        return datasets[0]

    dataset = client.create_dataset(DATASET_NAME, description="Eval queries for Deep Research Agent")
    for ex in EXAMPLES:
        client.create_example(
            inputs={"query": ex["query"]},
            dataset_id=dataset.id,
        )
    print(f"Created dataset '{DATASET_NAME}' with {len(EXAMPLES)} examples.")
    return dataset


def run_agent(inputs: dict) -> dict:
    """Target function: runs the research workflow and returns the final report."""
    query = inputs["query"]
    state = {
        "messages": [HumanMessage(content=query)],
        "original_query": query,
        "iteration": 0,
        "gathered_info": [],
    }

    workflow = DeepResearchWorkflow()
    result = None
    for event in workflow.graph.stream(state, {"configurable": {"thread_id": "eval"}}):
        for node, output in event.items():
            if node == "writer":
                for msg in output.get("messages", []):
                    result = msg.content

    return {"final_report": result or "No output"}


def main():
    create_dataset()

    print("Running evaluations...")
    results = evaluate(
        run_agent,
        data=DATASET_NAME,
        evaluators=[has_citations, report_length, has_markdown_headers, no_errors],
        experiment_prefix="deep-researcher",
    )
    print(f"Evaluation complete. View results in LangSmith Studio.")
    print(f"Results: {results}")


if __name__ == "__main__":
    main()
