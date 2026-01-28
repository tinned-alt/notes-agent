"""Vector store management for semantic search over notes."""

import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Set
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

    def _generate_doc_id(self, note_path: Path, chunk_index: int) -> str:
        """Generate a unique document ID for a note chunk.

        Args:
            note_path: Path to the note
            chunk_index: Index of the chunk within the note

        Returns:
            Unique document ID string
        """
        # Create a stable hash from the note path
        path_hash = hashlib.md5(str(note_path).encode()).hexdigest()[:12]
        return f"{path_hash}_chunk_{chunk_index}"

    def _get_note_doc_ids(self, note_path: Path) -> List[str]:
        """Get all document IDs associated with a specific note.

        Args:
            note_path: Path to the note

        Returns:
            List of document IDs for this note
        """
        try:
            collection = self.vector_store._collection
            # Query by metadata source field
            results = collection.get(
                where={"source": str(note_path)},
                include=[]
            )
            return results['ids'] if results and results['ids'] else []
        except Exception:
            return []

    def delete_note_from_index(self, note_path: Path) -> int:
        """Delete all chunks for a specific note from the index.

        Args:
            note_path: Path to the note to remove

        Returns:
            Number of documents deleted
        """
        doc_ids = self._get_note_doc_ids(note_path)
        if doc_ids:
            try:
                self.vector_store._collection.delete(ids=doc_ids)
                return len(doc_ids)
            except Exception:
                return 0
        return 0

    def add_note_to_index(self, note_path: Path) -> int:
        """Add a single note to the index.

        Args:
            note_path: Path to the note to add

        Returns:
            Number of chunks added
        """
        try:
            note_data = self.vault.read_note(note_path)
        except Exception:
            return 0

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

        documents = []
        doc_ids = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk'] = i
            doc_id = self._generate_doc_id(note_path, i)
            documents.append(Document(
                page_content=chunk,
                metadata=chunk_metadata
            ))
            doc_ids.append(doc_id)

        if documents:
            self.vector_store.add_documents(documents, ids=doc_ids)

        return len(documents)

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

    def update_note_index(self, note_path: Path) -> int:
        """Update the index for a specific note (delete and re-add).

        Args:
            note_path: Path to the note to update

        Returns:
            Number of chunks indexed for this note
        """
        # Delete existing chunks for this note
        self.delete_note_from_index(note_path)

        # Re-add the note
        return self.add_note_to_index(note_path)

    def sync_index(self) -> Dict[str, int]:
        """Synchronize the index with the current vault state.

        This is more efficient than index_all_notes() as it only updates
        notes that have changed, been added, or been removed.

        Returns:
            Dictionary with counts: {'added': N, 'removed': N, 'updated': N}
        """
        stats = {'added': 0, 'removed': 0, 'updated': 0, 'unchanged': 0}

        # Get all notes currently in vault
        vault_notes = set(str(p) for p in self.vault.get_all_notes())

        # Get all notes currently in index
        indexed_notes: Set[str] = set()
        try:
            collection = self.vector_store._collection
            results = collection.get(include=['metadatas'])
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata and 'source' in metadata:
                        indexed_notes.add(metadata['source'])
        except Exception:
            # If we can't read the index, do a full reindex
            self.index_all_notes()
            return {'added': len(vault_notes), 'removed': 0, 'updated': 0, 'unchanged': 0}

        # Find notes to add (in vault but not in index)
        notes_to_add = vault_notes - indexed_notes
        for note_path_str in notes_to_add:
            note_path = Path(note_path_str)
            if note_path.exists():
                self.add_note_to_index(note_path)
                stats['added'] += 1

        # Find notes to remove (in index but not in vault)
        notes_to_remove = indexed_notes - vault_notes
        for note_path_str in notes_to_remove:
            self.delete_note_from_index(Path(note_path_str))
            stats['removed'] += 1

        # For notes in both, we could check modification time, but for now
        # we'll leave them unchanged (full reindex handles updates)
        stats['unchanged'] = len(vault_notes & indexed_notes)

        return stats

    def get_indexed_note_count(self) -> int:
        """Get the number of unique notes in the index.

        Returns:
            Number of unique notes indexed
        """
        try:
            collection = self.vector_store._collection
            results = collection.get(include=['metadatas'])
            if results and results['metadatas']:
                unique_sources = set()
                for metadata in results['metadatas']:
                    if metadata and 'source' in metadata:
                        unique_sources.add(metadata['source'])
                return len(unique_sources)
        except Exception:
            pass
        return 0

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
