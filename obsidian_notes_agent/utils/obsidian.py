"""Utilities for working with Obsidian vault files."""

import re
from pathlib import Path
from typing import List, Dict, Optional, Set
import frontmatter
from datetime import datetime


class ObsidianVault:
    """Manager for Obsidian vault operations."""

    def __init__(self, vault_path: Path):
        """Initialize the vault manager.

        Args:
            vault_path: Path to the Obsidian vault directory
        """
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

    def get_all_notes(self) -> List[Path]:
        """Get all markdown files in the vault.

        Returns:
            List of paths to markdown files
        """
        return list(self.vault_path.rglob("*.md"))

    def read_note(self, note_path: Path) -> Dict[str, any]:
        """Read a note and extract its frontmatter and content.

        Args:
            note_path: Path to the note file

        Returns:
            Dictionary with 'metadata', 'content', and 'path' keys
        """
        with open(note_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        return {
            'metadata': dict(post.metadata),
            'content': post.content,
            'path': note_path,
            'title': note_path.stem
        }

    def write_note(self, title: str, content: str,
                   tags: Optional[List[str]] = None,
                   metadata: Optional[Dict] = None,
                   subfolder: str = "") -> Path:
        """Create or update a note in the vault.

        Args:
            title: Note title (will be used as filename)
            content: Note content (markdown)
            tags: List of tags to add
            metadata: Additional frontmatter metadata
            subfolder: Optional subfolder within vault

        Returns:
            Path to the created/updated note
        """
        # Sanitize filename
        filename = self._sanitize_filename(title) + ".md"

        # Determine full path
        if subfolder:
            note_dir = self.vault_path / subfolder
            note_dir.mkdir(parents=True, exist_ok=True)
        else:
            note_dir = self.vault_path

        note_path = note_dir / filename

        # Prepare frontmatter
        fm_data = metadata or {}
        if tags:
            fm_data['tags'] = tags
        fm_data['created'] = fm_data.get('created', datetime.now().isoformat())
        fm_data['updated'] = datetime.now().isoformat()

        # Create note with frontmatter
        post = frontmatter.Post(content, **fm_data)

        # Write to file
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        return note_path

    def update_note_metadata(self, note_path: Path,
                            tags: Optional[List[str]] = None,
                            metadata: Optional[Dict] = None) -> None:
        """Update the frontmatter of an existing note.

        Args:
            note_path: Path to the note
            tags: Tags to add/update
            metadata: Metadata to add/update
        """
        note_data = self.read_note(note_path)

        # Update metadata
        current_metadata = note_data['metadata']
        if tags:
            # Merge tags
            existing_tags = set(current_metadata.get('tags', []))
            existing_tags.update(tags)
            current_metadata['tags'] = list(existing_tags)

        if metadata:
            current_metadata.update(metadata)

        current_metadata['updated'] = datetime.now().isoformat()

        # Write back
        post = frontmatter.Post(note_data['content'], **current_metadata)
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    def extract_links(self, content: str) -> Set[str]:
        """Extract wiki-style links from note content.

        Args:
            content: Note content

        Returns:
            Set of linked note titles
        """
        # Match [[link]] and [[link|alias]]
        pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        matches = re.findall(pattern, content)
        return set(matches)

    def extract_tags(self, content: str) -> Set[str]:
        """Extract hashtags from note content.

        Args:
            content: Note content

        Returns:
            Set of tags (without #)
        """
        pattern = r'#([a-zA-Z0-9_/-]+)'
        matches = re.findall(pattern, content)
        return set(matches)

    def find_note_by_title(self, title: str) -> Optional[Path]:
        """Find a note by its title.

        Args:
            title: Note title to search for

        Returns:
            Path to the note if found, None otherwise
        """
        filename = self._sanitize_filename(title) + ".md"
        for note_path in self.get_all_notes():
            if note_path.name == filename or note_path.stem == title:
                return note_path
        return None

    def add_link_to_note(self, note_path: Path, link_title: str) -> None:
        """Add a wiki-style link to a note.

        Args:
            note_path: Path to the note to update
            link_title: Title of the note to link to
        """
        note_data = self.read_note(note_path)
        content = note_data['content']

        # Check if link already exists
        if f"[[{link_title}]]" in content:
            return

        # Add link at the end under "Related Notes" section
        if "## Related Notes" in content:
            content = content.replace(
                "## Related Notes",
                f"## Related Notes\n- [[{link_title}]]"
            )
        else:
            content += f"\n\n## Related Notes\n- [[{link_title}]]"

        # Write back
        post = frontmatter.Post(content, **note_data['metadata'])
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    @staticmethod
    def _sanitize_filename(title: str) -> str:
        """Sanitize a title for use as a filename.

        Args:
            title: Title to sanitize

        Returns:
            Sanitized filename (without extension)
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            title = title.replace(char, '-')

        # Remove leading/trailing spaces and dots
        title = title.strip('. ')

        return title
