"""Custom LangSmith evaluators for the research agent."""

from langsmith.schemas import Example, Run


def has_citations(run: Run, example: Example) -> dict:
    """Check if the report contains source citations like [1], [2], etc."""
    output = run.outputs.get("final_report", "")
    import re
    citations = re.findall(r"\[\d+\]", output)
    return {"key": "has_citations", "score": 1.0 if len(citations) >= 1 else 0.0}


def report_length(run: Run, example: Example) -> dict:
    """Check if the report has meaningful length (at least 200 chars)."""
    output = run.outputs.get("final_report", "")
    return {"key": "report_length", "score": 1.0 if len(output) >= 200 else 0.0}


def has_markdown_headers(run: Run, example: Example) -> dict:
    """Check if the report uses markdown headers for structure."""
    output = run.outputs.get("final_report", "")
    has_headers = "##" in output
    return {"key": "has_markdown_headers", "score": 1.0 if has_headers else 0.0}


def no_errors(run: Run, example: Example) -> dict:
    """Check that the run completed without errors."""
    output = run.outputs.get("final_report", "")
    has_error = output.startswith("Error:") or output == "No data found."
    return {"key": "no_errors", "score": 0.0 if has_error else 1.0}
