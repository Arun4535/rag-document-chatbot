# Build Flow

This document explains the project as a step-by-step build, from document upload to citation-backed answers.

## 1. Project Setup

The project is a Streamlit RAG chatbot with modular Python code.

```text
rag-document-chatbot/
  app.py
  rag/
  tests/
  evals/
  docs/
  data/
```

Streamlit handles the UI, while the `rag/` package contains the AI engineering logic: loading, chunking, embeddings, retrieval, and generation.

## 2. Document Upload

The user uploads documents from the Streamlit sidebar in `app.py`.

Supported file types:

```text
PDF
DOCX
TXT
```

Uploaded files are saved into:

```text
data/uploads/
```

After upload, the user clicks **Index documents** to start the RAG indexing pipeline.

## 3. Text Extraction

The document is passed to `rag/loader.py`.

The loader chooses the correct extraction method based on file type:

```text
PDF  -> PyMuPDF extracts text page by page
DOCX -> python-docx extracts paragraph text
TXT  -> normal UTF-8 text reading
```

Each extracted unit becomes a `DocumentPage` object with:

```text
text
source filename
page number when available
```

This metadata is important because it later becomes the citation shown to the user.

## 4. Chunking

The extracted text is passed to `rag/chunker.py`.

Large document text is split into smaller overlapping chunks.

Default settings:

```text
chunk size: 900 characters
chunk overlap: 150 characters
```

Overlap helps preserve meaning when an answer spans two neighboring chunks.

Each chunk stores:

```text
chunk text
source file
page number
chunk index
stable chunk id
```

## 5. Embeddings

Each chunk is converted into a vector using `rag/embeddings.py`.

The project uses FastEmbed with:

```text
BAAI/bge-small-en-v1.5
```

This is a local embedding model, so document indexing does not require paid embedding API calls.

The embedding turns text into a numerical vector that captures semantic meaning.

## 6. Vector Storage

The vectors and chunk metadata are saved by `rag/vector_store.py`.

The v1 project uses a lightweight local vector index:

```text
data/vector_store/chunks.json
data/vector_store/embeddings.npy
```

`chunks.json` stores chunk text and metadata.

`embeddings.npy` stores the NumPy embedding matrix.

This keeps the first version simple, inspectable, and easy to run on a local machine.

## 7. User Question

When the user asks a question in the Streamlit chat box, `app.py` calls:

```python
pipeline.answer(question)
```

The pipeline lives in `rag/pipeline.py`.

## 8. Query Embedding

The question is embedded using the same embedding model that was used for document chunks.

Example:

```text
How long is the warranty?
```

This question becomes a query vector.

## 9. Retrieval

The vector store compares the query vector against stored document vectors using cosine similarity.

It returns the most relevant chunks:

```text
top-k chunks
```

Each retrieved chunk includes:

```text
text
source filename
page number
chunk index
similarity distance
```

## 10. Claude Answer Generation

The retrieved chunks and the user question are sent to Claude in `rag/generator.py`.

Claude receives a strict system prompt:

```text
Answer only from the provided document context.
If the context is not enough, say you do not know.
Use bracket citations like [1], [2].
```

This keeps the answer grounded in the uploaded documents instead of relying on general model knowledge.

## 11. Answer With Citations

The Streamlit app displays:

```text
Claude's answer
source citations
retrieved snippets
source file
page number
similarity distance
```

This makes every answer traceable back to the original uploaded documents.

## End-to-End Flow

```text
Upload document
-> Extract text
-> Split text into chunks
-> Embed chunks
-> Store vectors and metadata
-> Ask a question
-> Embed the question
-> Retrieve top-k relevant chunks
-> Send retrieved context to Claude
-> Display answer with citations
```

## Interview Explanation

I built a document RAG chatbot with Streamlit and Claude. The app extracts text from uploaded PDFs, DOCX, and TXT files, chunks the text with overlap, creates local FastEmbed embeddings, stores vectors in a persistent local index, retrieves the most relevant chunks for each question, and sends only that retrieved context to Claude to generate citation-backed answers.

The project demonstrates the core RAG skills used in AI engineering roles: ingestion, chunking, embeddings, vector retrieval, prompt construction, grounded generation, citations, and evaluation-ready modular design.
