# Design Document

Firstly, thankyou for giving me the opportunity to do this project. This is a really intresting problem.

## Background & Motivation

I have actually done a similar project which is called Agentic AI research assistant which had many tools in its arsenal. But there were a few shortcommings in that project:

1. **Tools were rarely called** — Most of the tools were not called because it relied on the LLM to call that specific tool and mostly it called only a few tools.
2. **No structured plan** — The agent didnt followed a specific plan, it just took the query from the user and decided which tool to use. The problem with this is that there was no specific good query for the websearch tool to follow.
3. **Looping without critique** — The agent also had a loop in which the agent would again circle back to tool call without having any specific critique node, so it would sometimes just stuck in a loop where it called tools, got the output and then decided whether it had to stop or return to the start node again.

## Architecture

In this iteration of the project I am trying to solve these non deterministic problems. What I plan to do is use a **Plan → Research → Critique → Report** structure:

- First the there will be a **planning node** that will plan what query needs to be asked to the web search tool.
- Then the **web search tool** will fetch all the relevant pages from the internet.
- Then the **critique node** will tell whether the information received is sufficient enough to answer the query or no.
- If yes then the report is generated, else it will go back to the planning node again.
- I will also add in a **loop counter** so that the agent doesnt get stuck in a loop.

## Project Structure

I first structured the project as an installable Python package. This enables me to do absolute imports to prevent "ModuleNotFound" errors and it will also allow me to install all the necessary packages in the requirements.txt file.

The folder structure:

- **agent/** — houses the main agent code
- **tools/** — defines the tools
- **utils/** — contains the actual logic for the tools and some other helper codes
- **prompt_library/** — houses the prompts file which will store all the prompts needed for llm calls
- **models/** — stores the pydantic models
- **config/** — stores all the config needed during execution of the agent
- **evals/** — LangSmith evaluations

## Implementation Steps

### Logging

I added logging to the code so that I can keep track of what is happening in the code.

### Config Loader

I made the config loader first as it will be used every where in the code.

### Model Loader

I added the model loader file that will help me load the model for any node of the agent. I have added the Groq model which will allow me to first test the model on free limits by groq service. I later added the OpenAI model.

### Web Search

I built the web search util — the file that will actually search the internet and return the agent webpages. Then I moved on to make the web search tool out of the web search util.

### Prompts

I have thought to add the planner node, the critique node and the report node — all of which will require prompts:

- **Writer prompt** — requires the results of the searches as input and also the initial query by the user to answer the question and give the report answering the question.
- **Critique prompt** — requires the searched results and the initial query to answer whether the results are sufficient enough to answer the question or not.
- **Planner prompt** — requires the initial query to generate search query for the web search tool, but it will also require the previous feedback from the critique node if the previous search was not enough to answer the question and also it will require the conversation history if any followup questions are asked.

### Agent Workflow

Building the agent now and also the pydantic models that will be used to help me in data validation. In my previous research agent I have used ReAct structure where it simply calls the tools based on the query and returns the output. Now I will use the **Plan → Research → Critique (loop back to plan if necessary) → Report** structure. This is mostly a linear graph structure with a conditional edge between the critique and the plan nodes.

### Parallel Web Search

One improvement that I wanted to do on my previous project was to make the web search faster, as it was taking a lot of time to fetch multiple webpages. What I had planned to do is use a parallel execution where each query is searched parallely and LangChain does provide a functionality for parallel execution of the same node in a map reduce manner and I implemented this here.

### Streaming Service

I built the server which will run the streaming service. After the query is sent from the Streamlit app to the server it will be processed by the agent and the progress will be streamed back to the Streamlit app. This is something new that I did in the project.

### Configurability

- Added OpenAI model switching inside Streamlit so that the server will override the default config.
- Added more writer prompts so that we can have different kinds of report (Detailed, Concise, Academic, Bullet Points).
- Added functionality to change reporting style — just a simple prompt change in the writer code does the work.

## Challenges

One issue I ran into was with the critique node. The LLM was returning the string `"True"` instead of an actual boolean value, which broke the conditional edge because my check was comparing against a boolean. I had to add explicit bool conversion in the critique node to handle this. Small thing but it took me a while to figure out why the loop wasnt working properly.

## Known Shortcomings & Future Work

I wish I had more time to add more functionality but I am stopping here at 5 hours. Things I would add with more time:

- **Human-in-the-loop** — so that a human can review the plan before research is executed, just like Google Gemini deep research mode.
- **RAG capability** — so that the agent can use files provided by the user for research as well.
- **Conversation memory** — a memory tool so that long conversation history can be retained and fetched back whenever a query needs it, just like RAG but for conversation memory.
- **More thorough testing** — I would have liked to add unit tests for the individual components like the config loader, model loader and web search util but I ran out of time. The LangSmith evals cover the end to end flow but dont test the individual pieces.

## Evaluations

I added LangSmith tests to make sure that the agent is working as expected.
