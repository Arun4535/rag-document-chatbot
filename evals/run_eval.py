from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from rag.config import AppConfig
from rag.pipeline import RAGPipeline


def main() -> None:
    load_dotenv()
    questions_path = Path(__file__).with_name("questions.json")
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    pipeline = RAGPipeline(AppConfig.from_env())

    hits = 0
    for item in questions:
        response = pipeline.answer(item["question"])
        sources = {source.source for source in response.sources}
        hit = item["expected_source"] in sources
        hits += int(hit)
        print(f"Q: {item['question']}")
        print(f"Expected source: {item['expected_source']} | Retrieved: {sorted(sources)} | Hit: {hit}")
        print(f"Answer: {response.answer}\n")

    total = len(questions)
    print(f"Retrieval source hit rate: {hits}/{total} = {hits / total:.2%}")


if __name__ == "__main__":
    main()
