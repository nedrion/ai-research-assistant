import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.services.embedding_service import EmbeddingService
from src.repositories.vector_store import VectorRepository
from src.services.llm_service import LlmService
from src.services.rag_service import RagService
from src.cli import app as cli


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

    embedder = EmbeddingService(settings.embedding_model)
    vector_store = VectorRepository(settings.chroma_dir, settings.collection_name)

    if args.command == "models":
        cli.list_models()
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

    llm = LlmService(settings.ollama_base_url, settings.llm_model)

    if not llm.is_server_running():
        print("Error: Ollama is not running. Start it with 'ollama serve'")
        sys.exit(1)

    if not llm.has_model():
        available = llm.list_models()
        print(f"Error: Model '{settings.llm_model}' is not installed in Ollama.")
        print(f"Change LLM_MODEL in .env to one of: {', '.join(available) if available else '(none available)'}")
        print(f"Or pull it: ollama pull {settings.llm_model}")
        sys.exit(1)

    pipeline = RagService(embedder, vector_store, llm, settings.top_k)

    if args.command == "ingest":
        cli.ingest(pipeline, args.pdf_path)
    elif args.command == "ask":
        cli.ask(pipeline, args.question)
    elif args.command == "chat":
        cli.chat(pipeline)


if __name__ == "__main__":
    main()
