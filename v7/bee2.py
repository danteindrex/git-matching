
import asyncio
import os
from dotenv import load_dotenv
import requests

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from beeai_framework.backend.chat import ChatModel
from beeai_framework.tools.mcp import MCPTool
from beeai_framework.workflows.agent import AgentWorkflow, AgentWorkflowInput

# Load environment variables (ensure SONAR_API_KEY and SONAR_API_ENDPOINT are set)
load_dotenv()

async def create_sonar_tool() -> MCPTool:
    # 1. Configure and launch a local MCP server (Perplexity Sonar)
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-everything"],
        env={
            **os.environ,
            "SONAR_API_KEY": os.getenv("SONAR_API_KEY"),
            "SONAR_API_ENDPOINT": os.getenv("SONAR_API_ENDPOINT"),
        },
    )
    # 2. Establish a stdio MCP client connection to that server
    read_stream, write_stream = await stdio_client(server_params)
    session = ClientSession(read_stream, write_stream)
    await session.initialize()

    # 3. Discover and wrap all MCP-exposed tools
    tools = await MCPTool.from_client(session)
    # 4. Select the Perplexity Sonar tool by name prefix
    sonar_tool = next(t for t in tools if t.name.lower().startswith("sonar"))
    return sonar_tool

async def main() -> None:
    # Initialize the LLM model
    llm = ChatModel.from_name("ollama:qwen2.5:14b")

    # Create and register the Perplexity Sonar deep-research tool
    sonar_tool = await create_sonar_tool()

    # Build the agent workflow
    workflow = AgentWorkflow(name="Job Market Deep Research Assistant")
    workflow.add_agent(
        name="JobMarketResearcher",
        role="A specialist in job market analysis.",
        instructions="Use the Perplexity Sonar tool to perform deep research on job market trends, roles, and opportunities.",
        tools=[sonar_tool],
        llm=llm,
    )

    # Add a synthesizer agent to compile and summarize results
    workflow.add_agent(
        name="DataSynthesizer",
        role="A meticulous synthesizer of information.",
        instructions="Combine the deep research outputs into a coherent summary with actionable insights.",
        llm=llm,
    )

    # Define your research queries
    queries = [
        "Analyze current trends in software engineering job market in 2025.",
        "Identify emerging roles and skill demands for data scientists.",
        "Summarize geographical hotspots for AI research positions globally."
    ]
    inputs = [AgentWorkflowInput(prompt=q) for q in queries]

    # Execute the workflow and print intermediate and final results
    response = await workflow.run(inputs=inputs).on(
        "success",
        lambda data, event: print(f"\n-> Step '{data.step}' completed.\n{data.state.final_answer}\n"),
    )

    print("==== Final Deep Research Summary ====")
    print(response.result.final_answer)

if __name__ == "__main__":
    asyncio.run(main())

