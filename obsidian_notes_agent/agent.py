"""LangChain agent for Obsidian note management."""

from typing import List, Dict
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage
from rich.console import Console
from rich.markdown import Markdown

from obsidian_notes_agent.config import Settings
from obsidian_notes_agent.utils.obsidian import ObsidianVault
from obsidian_notes_agent.utils.vector_store import NoteVectorStore
from obsidian_notes_agent.tools.note_tools import get_note_tools


# System prompt for the agent
SYSTEM_PROMPT = """You are an intelligent assistant for managing an Obsidian note-taking vault.
Your role is to help users create, organize, search, and connect their notes effectively.

When working with notes:
1. Always search for existing notes before creating new ones to avoid duplicates
2. Suggest meaningful tags based on note content
3. Proactively suggest links between related notes
4. Use semantic search to find relevant information
5. Help maintain a well-organized knowledge base

Guidelines:
- Be concise but thorough in your responses
- When creating notes, suggest appropriate tags and related notes
- When asked to summarize, read the note first and provide a clear summary
- Always confirm successful operations with specific details
- Use the available tools to interact with the Obsidian vault
"""


class NotesAgent:
    """LangChain-powered agent for Obsidian notes."""

    def __init__(self, settings: Settings):
        """Initialize the notes agent.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.console = Console()

        # Initialize components
        self.vault = ObsidianVault(settings.obsidian_vault_path)
        self.vector_store = NoteVectorStore(
            settings.vector_store_path,
            self.vault
        )

        # Initialize LLM for content analysis
        from langchain_anthropic import ChatAnthropic
        self.llm = ChatAnthropic(
            model=settings.claude_model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=settings.temperature,
        )

        # Get tools (pass LLM for content ingestion)
        self.tools = get_note_tools(self.vault, self.vector_store, self.llm)

        # Create agent using the new create_agent API
        self.agent = create_agent(  # type: ignore[call-arg]
            model=settings.claude_model,
            tools=self.tools,
            system_prompt=SYSTEM_PROMPT,
        )

        # Store conversation history for chat mode
        self.conversation_history: List[Dict] = []

    def initialize_vector_store(self) -> None:
        """Initialize the vector store by indexing all notes."""
        self.console.print("[yellow]Initializing vector store...[/yellow]")
        num_docs = self.vector_store.index_all_notes()
        self.console.print(f"[green]Indexed {num_docs} document chunks[/green]")

    def run(self, query: str, use_history: bool = False) -> str:
        """Run the agent with a query.

        Args:
            query: User query
            use_history: Whether to use conversation history

        Returns:
            Agent response
        """
        try:
            # Prepare messages
            messages = []

            if use_history and self.conversation_history:
                messages.extend(self.conversation_history)

            messages.append({"role": "user", "content": query})

            # Invoke the agent
            result = self.agent.invoke({"messages": messages})

            # Extract response from the last message
            response_messages = result.get("messages", [])
            if response_messages:
                # Get the last AI message
                for msg in reversed(response_messages):
                    if hasattr(msg, 'content') and msg.content:
                        response = msg.content
                        break
                else:
                    response = "No response generated."
            else:
                response = "No response generated."

            # Update conversation history if using history
            if use_history:
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({"role": "assistant", "content": response})

                # Keep history manageable (last 10 exchanges)
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

            return response

        except Exception as e:
            error_msg = f"Error running agent: {str(e)}"
            self.console.print(f"[red]{error_msg}[/red]")
            return error_msg

    def chat(self) -> None:
        """Start an interactive chat session."""
        self.console.print(Markdown("# Obsidian Notes Agent"))
        self.console.print("[cyan]Type 'exit' or 'quit' to end the session[/cyan]")
        self.console.print("[cyan]Type 'reindex' to rebuild the vector store[/cyan]")
        self.console.print("[cyan]Type 'clear' to clear conversation history[/cyan]\n")

        while True:
            try:
                user_input = input("\n🗒️  You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break

                if user_input.lower() == 'reindex':
                    self.initialize_vector_store()
                    continue

                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    self.console.print("[green]Conversation history cleared[/green]")
                    continue

                self.console.print("\n🤖 Agent:", style="bold green")
                response = self.run(user_input, use_history=True)

                # Print response as markdown
                self.console.print(Markdown(response))

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
