"""Vector store management for semantic search over notes."""

from pathlib import Path
from typing import List, Dict, Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from obsidian_notes_agent.utils.obsidian import ObsidianVault


class NoteVectorStore:
    """Manages vector store for semantic search over notes."""

    def __init__(self, persist_directory: Path, vault: ObsidianVault):
        """Initialize the vector store.

        Args:
            persist_directory: Directory to store the vector database
            vault: ObsidianVault instance
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.vault = vault

        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Initialize or load vector store
        self.vector_store = Chroma(
            persist_directory=str(self.persist_directory),
            embedding_function=self.embeddings,
            collection_name="obsidian_notes"
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def index_all_notes(self) -> int:
        """Index all notes in the vault.

        Returns:
            Number of documents indexed
        """
        notes = self.vault.get_all_notes()
        documents = []

        for note_path in notes:
            note_data = self.vault.read_note(note_path)

            # Create metadata
            metadata = {
                'source': str(note_path),
                'title': note_data['title'],
                'tags': note_data['metadata'].get('tags', []),
                'created': note_data['metadata'].get('created', ''),
            }

            # Combine title and content for better search
            full_text = f"# {note_data['title']}\n\n{note_data['content']}"

            # Split into chunks
            chunks = self.text_splitter.split_text(full_text)

            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk'] = i
                documents.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))

        if documents:
            # Clear existing collection and add new documents
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(self.persist_directory),
                collection_name="obsidian_notes"
            )

        return len(documents)

    def search_notes(self, query: str, k: int = 5) -> List[Dict]:
        """Search notes using semantic similarity.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of matching documents with metadata
        """
        results = self.vector_store.similarity_search_with_score(query, k=k)

        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': score,
                'title': doc.metadata.get('title', 'Unknown'),
                'path': doc.metadata.get('source', '')
            })

        return formatted_results

    def update_note_index(self, note_path: Path) -> None:
        """Update the index for a specific note.

        Args:
            note_path: Path to the note to update
        """
        # For simplicity, re-index all notes
        # In production, you'd want to delete specific documents and re-add
        self.index_all_notes()

    def get_similar_notes(self, note_path: Path, k: int = 5) -> List[Dict]:
        """Find notes similar to a given note.

        Args:
            note_path: Path to the reference note
            k: Number of similar notes to return

        Returns:
            List of similar notes
        """
        note_data = self.vault.read_note(note_path)
        query = f"{note_data['title']}\n{note_data['content'][:500]}"

        results = self.search_notes(query, k=k + 1)

        # Filter out the source note itself
        filtered_results = [
            r for r in results
            if r['path'] != str(note_path)
        ][:k]

        return filtered_results
