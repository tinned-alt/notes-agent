"""Content loading utilities for various file formats and URLs."""

from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


class ContentLoader:
    """Load and extract content from various sources."""

    @staticmethod
    def load_from_url(url: str) -> Dict[str, any]:
        """Load content from a URL.

        Args:
            url: URL to fetch content from

        Returns:
            Dictionary with 'title', 'content', 'source', and 'metadata'
        """
        try:
            # Fetch the URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = soup.find('title')
            title = title.get_text().strip() if title else urlparse(url).path.strip('/')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = '\n'.join(chunk for chunk in chunks if chunk)

            return {
                'title': title,
                'content': content,
                'source': url,
                'source_type': 'url',
                'metadata': {
                    'url': url,
                    'domain': urlparse(url).netloc
                }
            }

        except Exception as e:
            raise ValueError(f"Failed to load URL {url}: {str(e)}")

    @staticmethod
    def load_from_pdf(file_path: str) -> Dict[str, any]:
        """Load content from a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with 'title', 'content', 'source', and 'metadata'
        """
        try:
            from pypdf import PdfReader

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            reader = PdfReader(str(path))

            # Extract text from all pages
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n\n"

            # Get metadata
            metadata = {}
            if reader.metadata:
                metadata = {
                    'author': reader.metadata.get('/Author', ''),
                    'title': reader.metadata.get('/Title', ''),
                    'subject': reader.metadata.get('/Subject', ''),
                    'creator': reader.metadata.get('/Creator', ''),
                }

            title = metadata.get('title') or path.stem

            return {
                'title': title,
                'content': content.strip(),
                'source': str(path),
                'source_type': 'pdf',
                'metadata': metadata
            }

        except ImportError:
            raise ImportError("pypdf is required for PDF processing. Install with: pip install pypdf")
        except Exception as e:
            raise ValueError(f"Failed to load PDF {file_path}: {str(e)}")

    @staticmethod
    def load_from_docx(file_path: str) -> Dict[str, any]:
        """Load content from a DOCX file.

        Args:
            file_path: Path to DOCX file

        Returns:
            Dictionary with 'title', 'content', 'source', and 'metadata'
        """
        try:
            from docx import Document

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            doc = Document(str(path))

            # Extract all paragraphs
            content = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])

            # Extract metadata
            core_properties = doc.core_properties
            metadata = {
                'author': core_properties.author or '',
                'title': core_properties.title or '',
                'subject': core_properties.subject or '',
                'keywords': core_properties.keywords or '',
            }

            title = metadata.get('title') or path.stem

            return {
                'title': title,
                'content': content,
                'source': str(path),
                'source_type': 'docx',
                'metadata': metadata
            }

        except ImportError:
            raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Failed to load DOCX {file_path}: {str(e)}")

    @staticmethod
    def load_from_pptx(file_path: str) -> Dict[str, any]:
        """Load content from a PowerPoint file.

        Args:
            file_path: Path to PPTX file

        Returns:
            Dictionary with 'title', 'content', 'source', and 'metadata'
        """
        try:
            from pptx import Presentation

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            prs = Presentation(str(path))

            # Extract text from all slides
            content_parts = []
            for i, slide in enumerate(prs.slides, 1):
                slide_text = f"## Slide {i}\n\n"
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text += shape.text + "\n"
                if slide_text.strip() != f"## Slide {i}":
                    content_parts.append(slide_text)

            content = "\n\n".join(content_parts)

            # Get metadata
            metadata = {
                'author': prs.core_properties.author or '',
                'title': prs.core_properties.title or '',
                'subject': prs.core_properties.subject or '',
            }

            title = metadata.get('title') or path.stem

            return {
                'title': title,
                'content': content,
                'source': str(path),
                'source_type': 'pptx',
                'metadata': metadata
            }

        except ImportError:
            raise ImportError("python-pptx is required for PPTX processing. Install with: pip install python-pptx")
        except Exception as e:
            raise ValueError(f"Failed to load PPTX {file_path}: {str(e)}")

    @staticmethod
    def load_from_markdown(file_path: str) -> Dict[str, any]:
        """Load content from a Markdown file.

        Args:
            file_path: Path to Markdown file

        Returns:
            Dictionary with 'title', 'content', 'source', and 'metadata'
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to extract title from first heading
        lines = content.split('\n')
        title = path.stem
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        return {
            'title': title,
            'content': content,
            'source': str(path),
            'source_type': 'markdown',
            'metadata': {}
        }

    @staticmethod
    def load_from_text(file_path: str) -> Dict[str, any]:
        """Load content from a plain text file.

        Args:
            file_path: Path to text file

        Returns:
            Dictionary with 'title', 'content', 'source', and 'metadata'
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Try to extract title from first non-empty line
        lines = content.split('\n')
        title = path.stem
        for line in lines:
            if line.strip():
                title = line.strip()[:100]  # Use first 100 chars of first line
                break

        return {
            'title': title,
            'content': content,
            'source': str(path),
            'source_type': 'text',
            'metadata': {}
        }

    @staticmethod
    def load_from_rtf(file_path: str) -> Dict[str, any]:
        """Load content from an RTF file.

        Args:
            file_path: Path to RTF file

        Returns:
            Dictionary with 'title', 'content', 'source', and 'metadata'
        """
        try:
            from striprtf.striprtf import rtf_to_text

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()

            content = rtf_to_text(rtf_content)

            # Try to extract title from first line
            lines = content.split('\n')
            title = path.stem
            for line in lines:
                if line.strip():
                    title = line.strip()[:100]
                    break

            return {
                'title': title,
                'content': content,
                'source': str(path),
                'source_type': 'rtf',
                'metadata': {}
            }

        except ImportError:
            raise ImportError("striprtf is required for RTF processing. Install with: pip install striprtf")
        except Exception as e:
            raise ValueError(f"Failed to load RTF {file_path}: {str(e)}")

    @staticmethod
    def load_content(source: str) -> Dict[str, any]:
        """Load content from a URL or file path.

        Automatically detects the source type and uses the appropriate loader.

        Args:
            source: URL or file path

        Returns:
            Dictionary with 'title', 'content', 'source', and 'metadata'
        """
        # Check if it's a URL
        if source.startswith(('http://', 'https://')):
            return ContentLoader.load_from_url(source)

        # Otherwise treat as file path
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File or URL not found: {source}")

        # Determine file type by extension
        extension = path.suffix.lower()

        loaders = {
            '.pdf': ContentLoader.load_from_pdf,
            '.docx': ContentLoader.load_from_docx,
            '.doc': ContentLoader.load_from_docx,
            '.pptx': ContentLoader.load_from_pptx,
            '.ppt': ContentLoader.load_from_pptx,
            '.md': ContentLoader.load_from_markdown,
            '.markdown': ContentLoader.load_from_markdown,
            '.txt': ContentLoader.load_from_text,
            '.rtf': ContentLoader.load_from_rtf,
        }

        loader = loaders.get(extension)
        if not loader:
            # Default to text loader for unknown types
            return ContentLoader.load_from_text(source)

        return loader(source)
