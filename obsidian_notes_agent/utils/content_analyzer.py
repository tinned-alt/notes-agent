"""Content analysis utilities for tag and folder suggestions."""

from typing import List, Dict, Set
import re
from langchain_anthropic import ChatAnthropic


class ContentAnalyzer:
    """Analyze content to suggest tags, folders, and related notes."""

    def __init__(self, llm: ChatAnthropic):
        """Initialize the content analyzer.

        Args:
            llm: Language model for content analysis
        """
        self.llm = llm

    def analyze_content(self, title: str, content: str, source_type: str) -> Dict[str, any]:
        """Analyze content to suggest tags, folder, and extract key information.

        Args:
            title: Content title
            content: Content text
            source_type: Type of source (url, pdf, docx, etc.)

        Returns:
            Dictionary with suggested tags, folder, and summary
        """
        # Truncate content if too long (keep first 4000 chars)
        analysis_content = content[:4000] if len(content) > 4000 else content

        prompt = f"""Analyze the following content and provide:
1. 3-7 relevant tags (single words or short phrases, lowercase, use hyphens for multi-word tags)
2. A suggested folder name (one or two words, lowercase, describing the general category)
3. A brief one-sentence summary

Content Title: {title}
Content Type: {source_type}
Content Preview:
{analysis_content}

Respond in the following format:
TAGS: tag1, tag2, tag3, tag4
FOLDER: folder-name
SUMMARY: One sentence summary here"""

        try:
            response = self.llm.invoke(prompt)
            result = self._parse_analysis_response(response.content)
            return result
        except Exception as e:
            # Fallback to basic analysis
            return self._basic_analysis(title, content, source_type)

    def _parse_analysis_response(self, response: str) -> Dict[str, any]:
        """Parse the LLM response for tags, folder, and summary.

        Args:
            response: LLM response text

        Returns:
            Dictionary with tags, folder, and summary
        """
        result = {
            'tags': [],
            'folder': '',
            'summary': ''
        }

        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('TAGS:'):
                tags_text = line.replace('TAGS:', '').strip()
                result['tags'] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            elif line.startswith('FOLDER:'):
                result['folder'] = line.replace('FOLDER:', '').strip()
            elif line.startswith('SUMMARY:'):
                result['summary'] = line.replace('SUMMARY:', '').strip()

        return result

    def _basic_analysis(self, title: str, content: str, source_type: str) -> Dict[str, any]:
        """Perform basic analysis without LLM.

        Args:
            title: Content title
            content: Content text
            source_type: Type of source

        Returns:
            Dictionary with basic tags, folder, and summary
        """
        # Extract basic tags from title and content
        words = re.findall(r'\b[a-z]{3,}\b', (title + ' ' + content[:500]).lower())
        word_freq = {}
        for word in words:
            if word not in {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'been'}:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top words as tags
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        tags = [word for word, _ in top_words]

        # Add source type as tag
        tags.append(source_type)

        # Basic folder suggestion
        folder = 'imported-content'

        # Basic summary (first sentence)
        sentences = content.split('.')
        summary = sentences[0][:200] if sentences else title

        return {
            'tags': tags,
            'folder': folder,
            'summary': summary
        }

    def suggest_related_notes(self, content: str, existing_notes_titles: List[str]) -> List[str]:
        """Suggest which existing notes might be related to this content.

        Args:
            content: Content text
            existing_notes_titles: List of existing note titles

        Returns:
            List of potentially related note titles
        """
        if not existing_notes_titles:
            return []

        # Truncate content for analysis
        analysis_content = content[:2000] if len(content) > 2000 else content

        # Limit to 20 notes for analysis
        notes_sample = existing_notes_titles[:20] if len(existing_notes_titles) > 20 else existing_notes_titles

        prompt = f"""Given this content, which of the following existing notes might be related?
Only list the titles of notes that are clearly related to the content topic.

Content Preview:
{analysis_content}

Existing Notes:
{chr(10).join(f"- {title}" for title in notes_sample)}

Respond with a comma-separated list of related note titles (just the titles, no explanations).
If none are related, respond with "NONE".
"""

        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()

            if response_text.upper() == 'NONE':
                return []

            # Parse the response
            related = [title.strip() for title in response_text.split(',')]
            # Filter to only include actual note titles
            related = [title for title in related if title in existing_notes_titles]
            return related[:5]  # Limit to 5 suggestions

        except Exception:
            # Fallback: simple keyword matching
            return self._basic_related_notes(content, existing_notes_titles)

    def _basic_related_notes(self, content: str, existing_notes_titles: List[str]) -> List[str]:
        """Simple keyword-based related notes suggestion.

        Args:
            content: Content text
            existing_notes_titles: List of existing note titles

        Returns:
            List of potentially related note titles
        """
        content_lower = content.lower()[:1000]
        related = []

        for title in existing_notes_titles[:20]:
            # Check if any significant word from title appears in content
            title_words = set(re.findall(r'\b[a-z]{4,}\b', title.lower()))
            if any(word in content_lower for word in title_words):
                related.append(title)
                if len(related) >= 5:
                    break

        return related
