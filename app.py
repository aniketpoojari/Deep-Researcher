"""Streamlit UI for Deep Research Agent."""

import streamlit as st
import requests
import json

st.set_page_config(page_title="Deep Research Agent", layout="wide")
st.title("Deep Research Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar config
with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("LLM Provider", ["openai", "groq"], index=0)
    config = {
        "num_searches": st.slider("Searches", 1, 5, 3),
        "max_iterations": st.slider("Max iterations", 1, 3, 2),
        "results_per_search": st.slider("Results per search", 1, 5, 3),
    }
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle input
if query := st.chat_input("What would you like to research?"):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        progress_container = st.empty()
        output = st.empty()

        try:
            with requests.post(
                "http://localhost:8000/research/stream",
                json={"query": query, "history": st.session_state.messages[:-1], "config": config, "provider": provider},
                stream=True, timeout=180
            ) as r:
                r.raise_for_status()
                steps, report = [], None

                for line in r.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if "error" in data:
                        st.error(data["error"])
                        break
                    if data["node"] == "writer":
                        report = data["content"]
                    else:
                        steps.append(f"**{data['node']}**: {data['content'][:100]}...")
                        progress_container.expander("Progress", expanded=True).markdown("\n\n".join(steps))

                if report:
                    # Collapse the progress expander instead of deleting it
                    progress_container.expander("Progress", expanded=False).markdown("\n\n".join(steps))
                    output.markdown(report)
                    st.session_state.messages.append({"role": "assistant", "content": report})

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Run: python main.py")
        except Exception as e:
            st.error(f"Error: {e}")
