import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import config
from src.embeddings.embedder import Embedder
from src.vector_store.store import VectorStore
from src.qa.llm_client import OllamaClient
from src.qa.pipeline import RAGPipeline
from src.ui import cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Research Assistant - RAG CLI")
    subparsers = parser.add_subparsers(dest="command")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a PDF document")
    ingest_parser.add_argument("pdf_path", help="Path to the PDF file")

    ask_parser = subparsers.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("question", help="Your question")

    subparsers.add_parser("chat", help="Start interactive chat session")
    subparsers.add_parser("models", help="List available Ollama models")
    subparsers.add_parser("clear", help="Delete all documents from vector store")
    subparsers.add_parser("status", help="Show vector store info")

    remove_parser = subparsers.add_parser("remove", help="Remove a specific PDF's chunks")
    remove_parser.add_argument("pdf_path", help="Source PDF filename to remove")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    embedder = Embedder(config.EMBEDDING_MODEL)
    vector_store = VectorStore(config.CHROMA_DIR, config.COLLECTION_NAME)

    if args.command == "models":
        cli.list_models(config)
        return
    if args.command == "status":
        cli.show_status(vector_store)
        return
    if args.command == "clear":
        cli.clear_store(vector_store)
        return
    if args.command == "remove":
        cli.remove_document(vector_store, args.pdf_path)
        return

    llm = OllamaClient(config.OLLAMA_BASE_URL, config.LLM_MODEL)

    if not llm.is_server_running():
        print("Error: Ollama is not running. Start it with 'ollama serve'")
        sys.exit(1)

    if not llm.has_model():
        available = llm.list_models()
        print(f"Error: Model '{config.LLM_MODEL}' is not installed in Ollama.")
        print(f"Change LLM_MODEL in .env to one of: {', '.join(available) if available else '(none available)'}")
        print(f"Or pull it: ollama pull {config.LLM_MODEL}")
        sys.exit(1)

    pipeline = RAGPipeline(embedder, vector_store, llm, config.TOP_K)

    if args.command == "ingest":
        cli.ingest(pipeline, args.pdf_path, config)
    elif args.command == "ask":
        cli.ask(pipeline, args.question)
    elif args.command == "chat":
        cli.chat(pipeline)


if __name__ == "__main__":
    main()
