"""Vector store management for semantic search over notes."""

import hashlib
import logging
import os
from pathlib import Path
from typing import List, Dict, Set
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from obsidian_notes_agent.utils.obsidian import ObsidianVault

logger = logging.getLogger(__name__)


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

        Raises:
            RuntimeError: If there's a database error (not just empty results)
        """
        try:
            collection = self.vector_store._collection
            # Query by metadata source field
            results = collection.get(
                where={"source": str(note_path)},
                include=[]
            )
            return results['ids'] if results and results['ids'] else []
        except Exception as e:
            logger.error(f"Failed to get document IDs for {note_path}: {e}")
            raise RuntimeError(f"Database error while querying note: {e}") from e

    def delete_note_from_index(self, note_path: Path) -> int:
        """Delete all chunks for a specific note from the index.

        Args:
            note_path: Path to the note to remove

        Returns:
            Number of documents deleted

        Raises:
            RuntimeError: If deletion fails due to database error
        """
        try:
            doc_ids = self._get_note_doc_ids(note_path)
        except RuntimeError:
            # Note not in index, nothing to delete
            return 0

        if doc_ids:
            try:
                self.vector_store._collection.delete(ids=doc_ids)
                return len(doc_ids)
            except Exception as e:
                logger.error(f"Failed to delete documents for {note_path}: {e}")
                raise RuntimeError(f"Database error while deleting note: {e}") from e
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
        except Exception as e:
            logger.warning(f"Failed to read note {note_path}: {e}")
            return 0

        # Get modification time for change detection
        try:
            mtime = os.path.getmtime(note_path)
        except OSError:
            mtime = 0

        # Create metadata
        metadata = {
            'source': str(note_path),
            'title': note_data['title'],
            'tags': note_data['metadata'].get('tags', []),
            'created': note_data['metadata'].get('created', ''),
            'mtime': mtime,
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
        doc_ids = []

        for note_path in notes:
            try:
                note_data = self.vault.read_note(note_path)
            except Exception as e:
                logger.warning(f"Failed to read note {note_path}: {e}")
                continue

            # Get modification time for change detection
            try:
                mtime = os.path.getmtime(note_path)
            except OSError:
                mtime = 0

            # Create metadata
            metadata = {
                'source': str(note_path),
                'title': note_data['title'],
                'tags': note_data['metadata'].get('tags', []),
                'created': note_data['metadata'].get('created', ''),
                'mtime': mtime,
            }

            # Combine title and content for better search
            full_text = f"# {note_data['title']}\n\n{note_data['content']}"

            # Split into chunks
            chunks = self.text_splitter.split_text(full_text)

            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk'] = i
                # Generate stable document ID for consistent updates
                doc_id = self._generate_doc_id(note_path, i)
                documents.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))
                doc_ids.append(doc_id)

        if documents:
            # Clear existing collection and add new documents with stable IDs
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(self.persist_directory),
                collection_name="obsidian_notes",
                ids=doc_ids
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
        notes that have changed, been added, or been removed. Uses file
        modification times to detect changes.

        Returns:
            Dictionary with counts: {'added': N, 'removed': N, 'updated': N, 'unchanged': N}
        """
        stats = {'added': 0, 'removed': 0, 'updated': 0, 'unchanged': 0}

        # Get all notes currently in vault with their modification times
        vault_notes: Dict[str, float] = {}
        for p in self.vault.get_all_notes():
            try:
                vault_notes[str(p)] = os.path.getmtime(p)
            except OSError:
                vault_notes[str(p)] = 0

        # Get all notes currently in index with their stored modification times
        indexed_notes: Dict[str, float] = {}
        try:
            collection = self.vector_store._collection
            results = collection.get(include=['metadatas'])
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata and 'source' in metadata:
                        source = metadata['source']
                        # Only store mtime once per note (first chunk seen)
                        if source not in indexed_notes:
                            indexed_notes[source] = metadata.get('mtime', 0)
        except Exception as e:
            # If we can't read the index, do a full reindex
            logger.warning(f"Failed to read index, performing full reindex: {e}")
            self.index_all_notes()
            return {'added': len(vault_notes), 'removed': 0, 'updated': 0, 'unchanged': 0}

        vault_paths = set(vault_notes.keys())
        indexed_paths = set(indexed_notes.keys())

        # Find notes to add (in vault but not in index)
        notes_to_add = vault_paths - indexed_paths
        for note_path_str in notes_to_add:
            note_path = Path(note_path_str)
            if note_path.exists():
                try:
                    self.add_note_to_index(note_path)
                    stats['added'] += 1
                except Exception as e:
                    logger.warning(f"Failed to add note {note_path}: {e}")

        # Find notes to remove (in index but not in vault)
        notes_to_remove = indexed_paths - vault_paths
        for note_path_str in notes_to_remove:
            try:
                self.delete_note_from_index(Path(note_path_str))
                stats['removed'] += 1
            except Exception as e:
                logger.warning(f"Failed to remove note {note_path_str}: {e}")

        # Check for modified notes (in both, but mtime changed)
        common_notes = vault_paths & indexed_paths
        for note_path_str in common_notes:
            vault_mtime = vault_notes[note_path_str]
            indexed_mtime = indexed_notes.get(note_path_str, 0)

            # If modification time changed, re-index the note
            if vault_mtime > indexed_mtime:
                try:
                    self.update_note_index(Path(note_path_str))
                    stats['updated'] += 1
                except Exception as e:
                    logger.warning(f"Failed to update note {note_path_str}: {e}")
            else:
                stats['unchanged'] += 1

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
