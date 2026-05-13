from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag.config import AppConfig
from rag.pipeline import RAGPipeline


load_dotenv()


st.set_page_config(
    page_title="Document RAG Chatbot",
    page_icon="",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def get_pipeline() -> RAGPipeline:
    config = AppConfig.from_env()
    return RAGPipeline(config)


def save_uploaded_file(upload_dir: Path, uploaded_file) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(uploaded_file.name).name
    destination = upload_dir / safe_name
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def initialize_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("indexed_documents", [])


def render_sidebar(pipeline: RAGPipeline) -> None:
    st.sidebar.header("Documents")
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDF, DOCX, or TXT files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    if st.sidebar.button("Index documents", type="primary", use_container_width=True):
        if not uploaded_files:
            st.sidebar.warning("Upload at least one document first.")
            return

        with st.spinner("Extracting, chunking, embedding, and indexing documents..."):
            summaries = []
            for uploaded_file in uploaded_files:
                saved_path = save_uploaded_file(pipeline.config.upload_dir, uploaded_file)
                summary = pipeline.index_document(saved_path)
                summaries.append(summary)
                st.session_state["indexed_documents"].append(summary)

        st.sidebar.success(f"Indexed {len(summaries)} document(s).")

    st.sidebar.divider()
    st.sidebar.subheader("Retrieval")
    pipeline.config.top_k = st.sidebar.slider("Top-k chunks", 2, 8, pipeline.config.top_k)

    if st.sidebar.button("Clear chat", use_container_width=True):
        st.session_state["messages"] = []

    if st.session_state["indexed_documents"]:
        st.sidebar.divider()
        st.sidebar.subheader("Indexed this session")
        for doc in st.session_state["indexed_documents"]:
            st.sidebar.caption(f"{doc.filename}: {doc.chunk_count} chunks")


def render_chat(pipeline: RAGPipeline) -> None:
    st.title("Document RAG Chatbot")
    st.caption("Ask questions over uploaded documents. Answers are grounded in retrieved chunks and include citations.")

    if not os.getenv("ANTHROPIC_API_KEY"):
        st.warning("Add ANTHROPIC_API_KEY to your .env file before asking questions.")

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.markdown(source)

    question = st.chat_input("Ask a question about your documents")
    if not question:
        return

    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving context and asking Claude..."):
            response = pipeline.answer(question)
        st.markdown(response.answer)

        source_lines = []
        if response.sources:
            with st.expander("Sources"):
                for index, source in enumerate(response.sources, start=1):
                    label = source.citation_label(index)
                    snippet = source.text.replace("\n", " ")
                    line = f"**{label}**  \nSimilarity distance: `{source.distance:.4f}`  \n{snippet[:700]}"
                    st.markdown(line)
                    source_lines.append(line)

    st.session_state["messages"].append(
        {"role": "assistant", "content": response.answer, "sources": source_lines}
    )


def main() -> None:
    initialize_state()
    pipeline = get_pipeline()
    render_sidebar(pipeline)
    render_chat(pipeline)


if __name__ == "__main__":
    main()
