
import asyncio
import os
from dotenv import load_dotenv
import requests

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from beeai_framework.backend.chat import ChatModel
from beeai_framework.tools.mcp import MCPTool
from beeai_framework.workflows.agent import AgentWorkflow, AgentWorkflowInput

# Load environment variables (ensure SONAR_API_KEY and SONAR_API_ENDPOINT are set)
load_dotenv()

# Define FastAPI app
app = FastAPI(
    title="Job Market Deep Research API",
    description="Expose the Perplexity Sonar research agent via HTTP",
    version="1.0.0"
)

# Request schema
class ResearchRequest(BaseModel):
    prompts: list[str]

# Response schema
class ResearchResponse(BaseModel):
    step_results: list[str]
    final_summary: str

# Global variables to hold initialized tools and workflow
sonar_tool: MCPTool | None = None
workflow: AgentWorkflow | None = None
llm: ChatModel | None = None

async def init_agent():
    global sonar_tool, workflow, llm
    if sonar_tool and workflow:
        return  # Already initialized

    # 1. Initialize LLM
    llm = ChatModel.from_name("ollama:qwen2.5:14b")

    # 2. Launch MCP server and client
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-everything"],
        env={**os.environ, "SONAR_API_KEY": os.getenv("SONAR_API_KEY"), "SONAR_API_ENDPOINT": os.getenv("SONAR_API_ENDPOINT")}
    )
    read_stream, write_stream = await stdio_client(server_params)
    session = ClientSession(read_stream, write_stream)
    await session.initialize()

    # 3. Discover and select Sonar tool
    tools = await MCPTool.from_client(session)
    sonar_tool = next(t for t in tools if t.name.lower().startswith("sonar"))

    # 4. Build workflow
    workflow = AgentWorkflow(name="Job Market Deep Research Assistant")
    workflow.add_agent(
        name="JobMarketResearcher",
        role="A specialist in job market analysis.",
        instructions="Use the Perplexity Sonar tool to perform deep research on job market trends, roles, and opportunities.",
        tools=[sonar_tool],
        llm=llm,
    )
    workflow.add_agent(
        name="DataSynthesizer",
        role="A meticulous synthesizer of information.",
        instructions="Combine the deep research outputs into a coherent summary with actionable insights.",
        llm=llm,
    )

@app.post("/research", response_model=ResearchResponse)
async def analyze_research(request: ResearchRequest):
    """
    Accepts a list of prompts to perform deep research and returns step-by-step outputs and a final summary.
    """
    await init_agent()
    if not workflow:
        raise HTTPException(status_code=500, detail="Agent workflow initialization failed")

    inputs = [AgentWorkflowInput(prompt=prompt) for prompt in request.prompts]
    step_outputs: list[str] = []

    # Run the workflow and collect intermediate results
    response = await workflow.run(inputs=inputs).on(
        "success",
        lambda data, event: step_outputs.append(f"Step '{data.step}': {data.state.final_answer}")
    )

    return ResearchResponse(
        step_results=step_outputs,
        final_summary=response.result.final_answer
    )

if __name__ == "__main__":
    # Run with uvicorn on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8007)
