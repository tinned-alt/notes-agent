# Obsidian Notes Agent

An intelligent AI agent powered by LangChain and Claude that helps you manage your Obsidian vault. The agent can create notes, search semantically across your knowledge base, suggest links between related notes, add tags, and more.

## Features

- **Create and Edit Notes**: Create new notes with intelligent tagging suggestions
- **Semantic Search**: Find notes based on meaning, not just keywords
- **Link Suggestions**: Discover connections between related notes
- **Auto-Tagging**: Automatically suggest and add relevant tags to notes
- **Summarization**: Generate summaries of individual notes or collections
- **Content Ingestion**: Import content from URLs and files (PDF, DOCX, PPTX, Markdown, RTF, TXT)
  - Automatic content analysis and tagging
  - Smart folder placement based on content
  - Auto-linking to related notes in your vault
  - Source tracking and metadata preservation
- **Natural Language Interface**: Interact with your notes using conversational commands

## Prerequisites

- Python 3.9 or higher
- An Obsidian vault
- Anthropic API key (for Claude)

## Installation

1. **Clone or navigate to the project directory**

```bash
cd notes-agent
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your configuration:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

## Usage

The agent provides multiple ways to interact with your notes:

### 1. Direct Content Ingestion (No Chat Required)

Quickly ingest content from URLs or files without entering chat mode:

```bash
# Ingest from URL
python main.py ingest https://example.com/article

# Ingest from file
python main.py ingest /path/to/document.pdf

# Ingest with custom title
python main.py ingest ~/Downloads/paper.pdf --title "Research Paper Summary"

# Ingest and reindex vector store
python main.py ingest https://blog.com/post --reindex
```

**Supported formats:** PDF, DOCX, PPTX, Markdown, RTF, TXT, and web pages

The agent will automatically:
- Extract and analyze the content
- Suggest relevant tags
- Place the note in an appropriate folder
- Link to related notes in your vault
- Preserve source metadata

### 2. Interactive Chat Mode

Start a conversational session to manage your notes:

```bash
python main.py chat
```

On first run, the agent will index all your notes (this may take a minute). Then you can interact naturally:

```
🗒️  You: Create a note about Python best practices
🗒️  You: Find all notes related to machine learning
🗒️  You: Suggest notes I should link to "Project Ideas"
🗒️  You: Add tags to my note about Docker
🗒️  You: Ingest this article: https://example.com/ai-trends
```

**Chat commands:**
- `exit` or `quit` - End the session
- `reindex` - Rebuild the vector store
- `clear` - Clear conversation history

### 3. Single Query Mode

Ask a single question without entering interactive mode:

```bash
python main.py query "What notes do I have about productivity?"
```

### 4. Reindex Vector Store

If you've added many notes outside the agent, rebuild the search index:

```bash
python main.py reindex
```

Or use the `--reindex` flag with other commands:

```bash
python main.py chat --reindex
python main.py ingest file.pdf --reindex
```

### 5. View Configuration

Check your current configuration:

```bash
python main.py info
```

## How It Works

### Tools Available to the Agent

The agent has access to these tools:

1. **create_note**: Create new notes with title, content, and tags
2. **search_notes**: Semantic search across all notes
3. **read_note**: Read the full content of a specific note
4. **update_note_metadata**: Add tags or metadata to existing notes
5. **suggest_links**: Find related notes that should be linked
6. **add_link**: Create wiki-style links between notes
7. **list_notes**: List all notes or filter by tag
8. **ingest_content**: Import content from URLs or files
   - Supported formats: PDF, DOCX, PPTX, Markdown, RTF, TXT, and web pages
   - Automatically analyzes content for tags and categorization
   - Suggests related notes and creates links
   - Places notes in appropriate folders based on content

### Vector Store

The agent uses a local vector database (ChromaDB) to enable semantic search. Notes are:
- Split into chunks
- Embedded using the `all-MiniLM-L6-v2` model
- Stored locally for fast retrieval

The vector store is automatically created on first run and can be updated with `reindex`.

## Example Workflows

### Quick Content Ingestion (CLI)

```bash
# Save an article from the web
python main.py ingest https://blog.com/ai-trends-2024

# Import a research paper
python main.py ingest ~/Downloads/transformer-paper.pdf -t "Attention Is All You Need"

# Import meeting notes
python main.py ingest ~/Documents/meeting-notes.docx
```

### Interactive Chat Queries

Start chat mode: `python main.py chat`

**Create a note:**
```
Create a note called "LangChain Tutorial" about building AI agents with LangChain.
Add tags for python, AI, and tutorial.
```

**Search notes:**
```
Find all my notes about machine learning algorithms
```

**Link related notes:**
```
What notes should I link to my "Deep Learning Basics" note?
```

**Summarize:**
```
Read my note "Project Ideas" and summarize it
```

**Add tags:**
```
Add the tags "work" and "important" to my "Q1 Goals" note
```

**Ingest in chat mode:**
```
Ingest this article: https://example.com/ai-trends-2024
Import this PDF: /home/user/Documents/research-paper.pdf
```

### Batch Processing

```bash
# Ingest multiple documents
for file in ~/Downloads/*.pdf; do
    python main.py ingest "$file"
done

# Rebuild index after batch ingestion
python main.py reindex
```

## Project Structure

```
notes-agent/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── agent.py               # Main agent implementation
│   ├── tools/
│   │   ├── __init__.py
│   │   └── note_tools.py      # LangChain tools for note operations
│   └── utils/
│       ├── __init__.py
│       ├── obsidian.py        # Obsidian vault utilities
│       ├── vector_store.py    # Vector store management
│       ├── content_loader.py  # Load content from URLs and files
│       └── content_analyzer.py # Analyze content for tags and links
├── data/                      # Vector database storage (created automatically)
├── main.py                    # CLI entry point
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Configuration Options

All options can be set in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `OBSIDIAN_VAULT_PATH` | Path to Obsidian vault | Required |
| `CLAUDE_MODEL` | Claude model to use | claude-sonnet-4-5-20250929 |
| `VECTOR_STORE_PATH` | Vector database location | ./data/chroma_db |
| `MAX_ITERATIONS` | Max agent iterations | 10 |
| `TEMPERATURE` | LLM temperature | 0.7 |

## Troubleshooting

**"Vault path does not exist" error**
- Check that `OBSIDIAN_VAULT_PATH` in `.env` points to your actual vault directory
- Use an absolute path, not a relative one

**Import errors**
- Make sure you've activated your virtual environment
- Run `pip install -r requirements.txt` again

**Vector store errors**
- Try rebuilding with `python main.py reindex`
- Delete the `data/` directory and let it rebuild

**Agent not finding notes**
- Run `python main.py reindex` to rebuild the search index
- Check that your vault path is correct with `python main.py info`

## Development

To extend the agent:

1. **Add new tools**: Edit `src/tools/note_tools.py`
2. **Modify agent behavior**: Edit the prompt in `src/agent.py`
3. **Add utilities**: Create new modules in `src/utils/`

## License

MIT

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
