import asyncio
import json
from datetime import datetime, timezone

import requests
from anthropic import AsyncAnthropic
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from config import get_settings


TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information about a topic.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": "Fetch and extract readable text from a web page.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "save_section",
        "description": "Save a section into the final report.",
        "input_schema": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
            "required": ["title", "content"],
        },
    },
]


class ResearchAgent:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.claude_model
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def run(self, topic: str):
        report = {"overview": "", "findings": [], "conclusion": "", "sources": []}
        messages = [
            {
                "role": "user",
                "content": (
                    f"Research this topic and build a concise report: {topic}. "
                    "Use tools to search, fetch useful pages, and save report sections. "
                    "Save Overview, Key Findings, Conclusion, and Sources."
                ),
            }
        ]

        start = datetime.now(timezone.utc)
        tool_calls = 0

        for _ in range(10):
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.2,
                tools=TOOLS,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_calls += 1
                yield self._event({"type": "tool_call", "tool": block.name, "input": block.input})
                result = await self._run_tool(block.name, block.input, report)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)[:3000]}
                )

            if not tool_results:
                break

            messages.append({"role": "user", "content": tool_results})

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        yield self._event(
            {
                "type": "complete",
                "tool_calls": tool_calls,
                "time_taken": round(elapsed, 2),
                "report": report,
            }
        )

    async def _run_tool(self, name: str, tool_input: dict, report: dict) -> dict:
        if name == "web_search":
            return await asyncio.to_thread(web_search, tool_input["query"])
        if name == "fetch_page":
            result = await asyncio.to_thread(fetch_page, tool_input["url"])
            if result.get("url"):
                report["sources"].append(result["url"])
            return result
        if name == "save_section":
            save_section(report, tool_input["title"], tool_input["content"])
            return {"saved": tool_input["title"]}
        return {"error": f"Unknown tool: {name}"}

    def _event(self, payload: dict) -> str:
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        return f"data: {json.dumps(payload)}\n\n"


def web_search(query: str) -> dict:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    return {
        "results": [
            {"title": item.get("title", ""), "url": item.get("href", ""), "snippet": item.get("body", "")}
            for item in results
        ]
    }


def fetch_page(url: str) -> dict:
    response = requests.get(url, timeout=10, headers={"User-Agent": "DocSenseResearchAgent/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return {"url": url, "text": text[:2000]}


def save_section(report: dict, title: str, content: str) -> None:
    normalized = title.strip().lower()
    if "overview" in normalized:
        report["overview"] = content
    elif "conclusion" in normalized:
        report["conclusion"] = content
    elif "source" in normalized:
        report["sources"].append(content)
    else:
        report["findings"].append({"title": title, "content": content})
