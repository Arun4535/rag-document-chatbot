# Architecture

This project is a modular Retrieval-Augmented Generation chatbot for private documents.

```text
Document upload
  -> loader extracts text from PDF, DOCX, or TXT
  -> chunker splits text with overlap and metadata
  -> FastEmbed creates local embeddings
  -> local vector index stores vectors and chunk metadata
  -> retriever finds top-k relevant chunks for each question
  -> Claude generates an answer grounded in retrieved context
  -> Streamlit displays the answer, citations, and retrieved snippets
```

## Key Design Choices

- Streamlit keeps the interface Python-only and easy to demo.
- Claude handles final answer generation, where reasoning quality matters most.
- FastEmbed keeps local embeddings lightweight and avoids paid embedding APIs.
- A simple persistent vector index keeps the first version easy to run and inspect.
- Citations are preserved through chunk metadata: source file, page, and chunk index.

## Production Extensions

- Add authentication and per-user collections.
- Add background indexing for large files.
- Add ChromaDB, Qdrant, or Pinecone as a production vector database.
- Add reranking after vector search.
- Add hybrid keyword plus vector retrieval.
- Add answer quality evaluation with a labeled question set.
