# Document RAG Chatbot

A Streamlit Retrieval-Augmented Generation app for asking questions over private documents. It extracts text from uploaded files, chunks the content, stores local embeddings in a persistent vector index, retrieves relevant chunks, and asks Claude to generate citation-backed answers.

## Features

- Upload PDF, DOCX, and TXT files
- Chunk documents with overlap and source metadata
- Create local embeddings with `fastembed`
- Store vectors in a persistent local vector index
- Ask questions through a Streamlit chat UI
- Generate grounded answers with Claude
- Show citations and retrieved snippets
- Includes basic tests and an evaluation script starter

## Tech Stack

- UI: Streamlit
- LLM: Anthropic Claude
- Embeddings: FastEmbed
- Vector index: NumPy-backed local storage
- Document parsing: PyMuPDF, python-docx
- Tests: pytest

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add your Anthropic key to `.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
```

## Run

```bash
streamlit run app.py
```

Then open the local URL printed by Streamlit.

## Quick Test

The repo includes a small synthetic test document:

```text
sample_docs/company_handbook.txt
```

Use it to test the app:

1. Start Streamlit.
2. Upload `sample_docs/company_handbook.txt` in the sidebar.
3. Click **Index documents**.
4. Ask questions like:

```text
How many days per week can employees work remotely?
What is the annual learning budget?
How quickly must critical support issues be acknowledged?
```

The app should answer using the handbook and show `company_handbook.txt` in the sources.

## How It Works

1. Upload documents in the sidebar.
2. Click **Index documents**.
3. Ask questions in the chat input.
4. The app embeds your question, retrieves relevant chunks, and sends only those chunks to Claude.
5. Claude answers using the retrieved context and cites the supporting chunks.

## Portfolio Talking Points

- The project separates ingestion, chunking, embedding, retrieval, and generation into testable modules.
- It uses Claude only for grounded response generation while using local embeddings for cost-effective retrieval.
- Citations are generated from chunk metadata to make answers inspectable.
- The architecture can be extended with ChromaDB/Qdrant, reranking, hybrid search, auth, and evaluation dashboards.
