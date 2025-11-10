"""LangChain tools for Obsidian note operations."""

from typing import Optional, List, Dict
from pathlib import Path
from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from pydantic import Field
from obsidian_notes_agent.utils.obsidian import ObsidianVault
from obsidian_notes_agent.utils.vector_store import NoteVectorStore
from obsidian_notes_agent.utils.content_loader import ContentLoader
from obsidian_notes_agent.utils.content_analyzer import ContentAnalyzer


class CreateNoteTool(BaseTool):
    """Tool for creating a new note in the Obsidian vault."""

    name: str = "create_note"
    description: str = """
    Create a new note in the Obsidian vault.
    Input should be a JSON string with 'title', 'content', and optionally 'tags' (list) and 'subfolder'.
    Example: {"title": "My Note", "content": "Note content here", "tags": ["important", "work"]}
    """

    vault: ObsidianVault = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, tool_input: str) -> str:
        """Create a note."""
        import json
        try:
            data = json.loads(tool_input)
            title = data.get('title')
            content = data.get('content')
            tags = data.get('tags', [])
            subfolder = data.get('subfolder', '')

            if not title or not content:
                return "Error: Both 'title' and 'content' are required."

            note_path = self.vault.write_note(
                title=title,
                content=content,
                tags=tags,
                subfolder=subfolder
            )

            return f"Successfully created note: {note_path.name} at {note_path}"

        except json.JSONDecodeError:
            return "Error: Invalid JSON input. Please provide valid JSON."
        except Exception as e:
            return f"Error creating note: {str(e)}"


class SearchNotesTool(BaseTool):
    """Tool for searching notes using semantic search."""

    name: str = "search_notes"
    description: str = """
    Search for notes using semantic search. This finds notes based on meaning, not just keywords.
    Input should be a search query string.
    Example: "notes about machine learning"
    """

    vector_store: NoteVectorStore = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        """Search notes."""
        try:
            results = self.vector_store.search_notes(query, k=5)

            if not results:
                return "No notes found matching your query."

            output = "Found the following notes:\n\n"
            for i, result in enumerate(results, 1):
                output += f"{i}. **{result['title']}**\n"
                output += f"   Path: {result['path']}\n"
                output += f"   Relevance: {1 - result['score']:.2f}\n"
                output += f"   Preview: {result['content'][:200]}...\n\n"

            return output

        except Exception as e:
            return f"Error searching notes: {str(e)}"


class ReadNoteTool(BaseTool):
    """Tool for reading the content of a specific note."""

    name: str = "read_note"
    description: str = """
    Read the full content of a specific note by its title.
    Input should be the note title (without .md extension).
    Example: "My Daily Journal"
    """

    vault: ObsidianVault = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, title: str) -> str:
        """Read a note."""
        try:
            note_path = self.vault.find_note_by_title(title)

            if not note_path:
                return f"Note '{title}' not found in vault."

            note_data = self.vault.read_note(note_path)

            output = f"# {note_data['title']}\n\n"
            if note_data['metadata']:
                output += "**Metadata:**\n"
                for key, value in note_data['metadata'].items():
                    output += f"- {key}: {value}\n"
                output += "\n"

            output += f"**Content:**\n{note_data['content']}\n"

            return output

        except Exception as e:
            return f"Error reading note: {str(e)}"


class UpdateNoteMetadataTool(BaseTool):
    """Tool for updating note metadata (tags, etc.)."""

    name: str = "update_note_metadata"
    description: str = """
    Update the metadata of an existing note (add tags, etc.).
    Input should be JSON with 'title' and optionally 'tags' (list to add) or 'metadata' (dict).
    Example: {"title": "My Note", "tags": ["important", "reviewed"]}
    """

    vault: ObsidianVault = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, tool_input: str) -> str:
        """Update note metadata."""
        import json
        try:
            data = json.loads(tool_input)
            title = data.get('title')

            if not title:
                return "Error: 'title' is required."

            note_path = self.vault.find_note_by_title(title)
            if not note_path:
                return f"Note '{title}' not found."

            tags = data.get('tags')
            metadata = data.get('metadata')

            self.vault.update_note_metadata(note_path, tags=tags, metadata=metadata)

            return f"Successfully updated metadata for note: {title}"

        except json.JSONDecodeError:
            return "Error: Invalid JSON input."
        except Exception as e:
            return f"Error updating metadata: {str(e)}"


class SuggestLinksTool(BaseTool):
    """Tool for suggesting related notes to link."""

    name: str = "suggest_links"
    description: str = """
    Suggest related notes that could be linked to a given note.
    Input should be the note title.
    Example: "Machine Learning Basics"
    """

    vault: ObsidianVault = Field(exclude=True)
    vector_store: NoteVectorStore = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, title: str) -> str:
        """Suggest links for a note."""
        try:
            note_path = self.vault.find_note_by_title(title)

            if not note_path:
                return f"Note '{title}' not found."

            similar_notes = self.vector_store.get_similar_notes(note_path, k=5)

            if not similar_notes:
                return "No related notes found."

            output = f"Suggested notes to link from '{title}':\n\n"
            for i, note in enumerate(similar_notes, 1):
                output += f"{i}. **{note['title']}**\n"
                output += f"   Path: {note['path']}\n"
                output += f"   Similarity: {1 - note['score']:.2f}\n\n"

            return output

        except Exception as e:
            return f"Error suggesting links: {str(e)}"


class AddLinkToNoteTool(BaseTool):
    """Tool for adding a link between two notes."""

    name: str = "add_link"
    description: str = """
    Add a wiki-style link from one note to another.
    Input should be JSON with 'from_note' and 'to_note' (both titles).
    Example: {"from_note": "Note A", "to_note": "Note B"}
    """

    vault: ObsidianVault = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, tool_input: str) -> str:
        """Add a link between notes."""
        import json
        try:
            data = json.loads(tool_input)
            from_note = data.get('from_note')
            to_note = data.get('to_note')

            if not from_note or not to_note:
                return "Error: Both 'from_note' and 'to_note' are required."

            from_path = self.vault.find_note_by_title(from_note)
            if not from_path:
                return f"Source note '{from_note}' not found."

            # Check if target note exists
            to_path = self.vault.find_note_by_title(to_note)
            if not to_path:
                return f"Target note '{to_note}' not found."

            self.vault.add_link_to_note(from_path, to_note)

            return f"Successfully added link from '{from_note}' to '{to_note}'"

        except json.JSONDecodeError:
            return "Error: Invalid JSON input."
        except Exception as e:
            return f"Error adding link: {str(e)}"


class ListNotesTool(BaseTool):
    """Tool for listing all notes in the vault."""

    name: str = "list_notes"
    description: str = """
    List all notes in the Obsidian vault.
    Input should be 'all' or a tag name to filter by (e.g., 'work').
    """

    vault: ObsidianVault = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, filter_input: str = "all") -> str:
        """List notes."""
        try:
            all_notes = self.vault.get_all_notes()

            if filter_input and filter_input.lower() != "all":
                # Filter by tag
                filtered_notes = []
                for note_path in all_notes:
                    note_data = self.vault.read_note(note_path)
                    tags = note_data['metadata'].get('tags', [])
                    if filter_input in tags:
                        filtered_notes.append(note_path)
                all_notes = filtered_notes

            if not all_notes:
                return "No notes found."

            output = f"Found {len(all_notes)} notes:\n\n"
            for note_path in sorted(all_notes)[:50]:  # Limit to 50
                relative_path = note_path.relative_to(self.vault.vault_path)
                output += f"- {relative_path}\n"

            if len(all_notes) > 50:
                output += f"\n... and {len(all_notes) - 50} more notes."

            return output

        except Exception as e:
            return f"Error listing notes: {str(e)}"


class IngestContentTool(BaseTool):
    """Tool for ingesting content from URLs or files into Obsidian."""

    name: str = "ingest_content"
    description: str = """
    Ingest content from a URL or file path and create a note in Obsidian.
    Supports URLs, PDF, DOCX, PPTX, Markdown, RTF, and TXT files.
    The tool will automatically analyze content, suggest tags, determine the best folder,
    and link to related notes.
    Input should be a JSON string with 'source' (URL or file path) and optionally 'custom_title'.
    Example: {"source": "https://example.com/article", "custom_title": "My Custom Title"}
    Example: {"source": "/path/to/document.pdf"}
    """

    vault: ObsidianVault = Field(exclude=True)
    vector_store: NoteVectorStore = Field(exclude=True)
    llm: ChatAnthropic = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, tool_input: str) -> str:
        """Ingest content from URL or file."""
        import json
        try:
            data = json.loads(tool_input)
            source = data.get('source')
            custom_title = data.get('custom_title')

            if not source:
                return "Error: 'source' (URL or file path) is required."

            # Load content
            try:
                content_data = ContentLoader.load_content(source)
            except Exception as e:
                return f"Error loading content: {str(e)}"

            # Use custom title if provided
            if custom_title:
                content_data['title'] = custom_title

            # Analyze content for tags, folder, and summary
            analyzer = ContentAnalyzer(self.llm)
            analysis = analyzer.analyze_content(
                content_data['title'],
                content_data['content'],
                content_data['source_type']
            )

            # Get all existing notes for related note suggestions
            existing_notes = self.vault.get_all_notes()
            existing_titles = [note.stem for note in existing_notes]

            # Suggest related notes
            related_notes = analyzer.suggest_related_notes(
                content_data['content'],
                existing_titles
            )

            # Format the note content
            note_content = self._format_note_content(
                content_data,
                analysis,
                related_notes
            )

            # Prepare tags
            tags = analysis.get('tags', [])
            tags.append(content_data['source_type'])  # Add source type as tag
            tags = list(set(tags))  # Remove duplicates

            # Add source metadata
            metadata = content_data.get('metadata', {})
            metadata['source'] = content_data['source']
            metadata['source_type'] = content_data['source_type']
            if analysis.get('summary'):
                metadata['summary'] = analysis['summary']

            # Create the note
            folder = analysis.get('folder', 'imported')
            note_path = self.vault.write_note(
                title=content_data['title'],
                content=note_content,
                tags=tags,
                metadata=metadata,
                subfolder=folder
            )

            # Add links to related notes
            if related_notes:
                for related_title in related_notes:
                    try:
                        self.vault.add_link_to_note(note_path, related_title)
                    except:
                        pass  # Skip if linking fails

            # Update vector store to include new note
            self.vector_store.update_note_index(note_path)

            # Build response
            response = f"Successfully ingested content and created note: {content_data['title']}\n\n"
            response += f"📁 Folder: {folder}\n"
            response += f"🏷️  Tags: {', '.join(tags)}\n"
            response += f"📝 Path: {note_path}\n"

            if related_notes:
                response += f"\n🔗 Linked to related notes:\n"
                for related in related_notes:
                    response += f"  - {related}\n"

            return response

        except json.JSONDecodeError:
            return "Error: Invalid JSON input. Please provide valid JSON with 'source' field."
        except Exception as e:
            return f"Error ingesting content: {str(e)}"

    def _format_note_content(self, content_data: Dict, analysis: Dict, related_notes: List[str]) -> str:
        """Format the note content with metadata and links.

        Args:
            content_data: Loaded content data
            analysis: Content analysis results
            related_notes: List of related note titles

        Returns:
            Formatted markdown content
        """
        parts = []

        # Add summary if available
        if analysis.get('summary'):
            parts.append(f"> {analysis['summary']}\n")

        # Add source information
        parts.append(f"**Source:** {content_data['source']}\n")
        parts.append(f"**Type:** {content_data['source_type']}\n")

        # Add original metadata if available
        if content_data.get('metadata'):
            meta = content_data['metadata']
            if meta.get('author'):
                parts.append(f"**Author:** {meta['author']}\n")
            if meta.get('domain'):
                parts.append(f"**Domain:** {meta['domain']}\n")

        parts.append("\n---\n\n")

        # Add main content
        parts.append(content_data['content'])

        # Add related notes section if any
        if related_notes:
            parts.append("\n\n## Related Notes\n")
            for related in related_notes:
                parts.append(f"- [[{related}]]\n")

        return "".join(parts)


def get_note_tools(vault: ObsidianVault, vector_store: NoteVectorStore, llm: Optional[ChatAnthropic] = None) -> List[BaseTool]:
    """Get all note tools configured with vault and vector store.

    Args:
        vault: ObsidianVault instance
        vector_store: NoteVectorStore instance
        llm: Optional ChatAnthropic instance for content analysis

    Returns:
        List of configured tools
    """
    tools = [
        CreateNoteTool(vault=vault),
        SearchNotesTool(vector_store=vector_store),
        ReadNoteTool(vault=vault),
        UpdateNoteMetadataTool(vault=vault),
        SuggestLinksTool(vault=vault, vector_store=vector_store),
        AddLinkToNoteTool(vault=vault),
        ListNotesTool(vault=vault),
    ]

    # Add IngestContentTool if LLM is provided
    if llm:
        tools.append(IngestContentTool(vault=vault, vector_store=vector_store, llm=llm))

    return tools
