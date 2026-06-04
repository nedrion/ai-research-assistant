from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from src.core.config import settings
from src.services.llm_service import LlmService

console = Console()


def list_models():
    llm = LlmService(settings.ollama_base_url)
    if not llm.is_server_running():
        console.print("[red]Ollama is not running. Start it with 'ollama serve'[/red]")
        return

    models = llm.list_models()
    if models:
        console.print("[bold]Available Ollama models:[/bold]")
        for m in models:
            marker = "[green]*[/green]" if m == settings.llm_model else " "
            console.print(f"  {marker} {m}")
        console.print(f"\nSet LLM_MODEL in .env to switch. Current: [bold]{settings.llm_model}[/bold]")
    else:
        console.print("No models found. Pull one with 'ollama pull <model>'")


def ingest(pipeline, pdf_path: str):
    path = Path(pdf_path)
    if not path.exists():
        console.print(f"[red]File not found: {pdf_path}[/red]")
        return

    with console.status(f"[bold green]Ingesting {path.name}...") as status:
        chunk_count = pipeline.ingest(str(path), settings.chunk_size, settings.chunk_overlap)

    total = pipeline.vector_store.count()
    console.print(f"[green]OK[/green] Ingested [bold]{path.name}[/bold] - {chunk_count} chunks created")
    console.print(f"[dim]Total chunks in store: {total}[/dim]")


def ask(pipeline, question: str):
    with console.status("[bold yellow]Thinking...") as status:
        result = pipeline.ask(question)

    console.print()
    console.print(Panel(Markdown(result["answer"]), title="Answer", border_style="green"))
    if result["sources"]:
        console.print("\n[dim]Sources:[/dim]")
        for s in result["sources"]:
            console.print(f"  [dim]- {s['source']} (chunk {s['chunk_index']})[/dim]")
    console.print()


def show_status(vector_store):
    count = vector_store.count()
    sources = vector_store.list_sources()
    console.print(f"[bold]Vector Store[/bold] — {count} total chunks")
    if sources:
        console.print("\n[dim]Sources:[/dim]")
        for src, n in sorted(sources.items()):
            console.print(f"  [dim]- {Path(src).name} ({n} chunks)[/dim]")
    else:
        console.print("[dim]No documents stored.[/dim]")


def clear_store(vector_store):
    confirm = Prompt.ask("[yellow]Delete ALL documents from the vector store?[/yellow]", choices=["y", "n"], default="n")
    if confirm == "y":
        vector_store.clear()
        console.print("[green]Vector store cleared.[/green]")
    else:
        console.print("[dim]Cancelled.[/dim]")


def remove_document(vector_store, pdf_path: str):
    removed = vector_store.delete_by_source(pdf_path)
    if removed > 0:
        console.print(f"[green]Removed {removed} chunks from '{Path(pdf_path).name}'[/green]")
    else:
        console.print(f"[yellow]No chunks found for '{Path(pdf_path).name}'[/yellow]")


def chat(pipeline):
    console.print(Panel.fit("[bold]AI Research Assistant[/bold]\nType 'exit' or 'quit' to stop.", border_style="blue"))

    while True:
        question = Prompt.ask("\n[bold cyan]You[/bold cyan]")
        if question.lower() in ("exit", "quit", "q"):
            break
        if not question.strip():
            continue

        with console.status("[bold yellow]Thinking...") as status:
            result = pipeline.ask(question)

        console.print(f"\n[bold green]Assistant[/bold green]")
        console.print(Panel(Markdown(result["answer"]), border_style="green"))
        if result["sources"]:
            console.print("[dim]Sources:[/dim] " + ", ".join(f"{s['source']}#{s['chunk_index']}" for s in result["sources"]))
