class ObsidianNotesAgent < Formula
  include Language::Python::Virtualenv

  desc "AI-powered agent for managing Obsidian notes with Claude"
  homepage "https://github.com/yourusername/obsidian-notes-agent"
  url "https://github.com/yourusername/obsidian-notes-agent/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "YOUR_SHA256_HERE"  # Calculate this after creating a release
  license "MIT"

  depends_on "python@3.12"

  # List all Python dependencies from pyproject.toml
  resource "langchain" do
    url "https://files.pythonhosted.org/packages/source/l/langchain/langchain-0.3.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "langchain-anthropic" do
    url "https://files.pythonhosted.org/packages/source/l/langchain-anthropic/langchain_anthropic-0.1.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "langchain-community" do
    url "https://files.pythonhosted.org/packages/source/l/langchain-community/langchain_community-0.0.20.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "langgraph" do
    url "https://files.pythonhosted.org/packages/source/l/langgraph/langgraph-0.6.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "chromadb" do
    url "https://files.pythonhosted.org/packages/source/c/chromadb/chromadb-0.4.22.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "sentence-transformers" do
    url "https://files.pythonhosted.org/packages/source/s/sentence-transformers/sentence-transformers-2.3.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/source/p/python-dotenv/python-dotenv-1.0.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.5.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "pydantic-settings" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic-settings/pydantic_settings-2.1.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/pyyaml-6.0.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "python-frontmatter" do
    url "https://files.pythonhosted.org/packages/source/p/python-frontmatter/python-frontmatter-1.1.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "pypdf" do
    url "https://files.pythonhosted.org/packages/source/p/pypdf/pypdf-4.0.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "python-docx" do
    url "https://files.pythonhosted.org/packages/source/p/python-docx/python-docx-1.1.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "python-pptx" do
    url "https://files.pythonhosted.org/packages/source/p/python-pptx/python-pptx-0.6.23.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "striprtf" do
    url "https://files.pythonhosted.org/packages/source/s/striprtf/striprtf-0.0.26.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "beautifulsoup4" do
    url "https://files.pythonhosted.org/packages/source/b/beautifulsoup4/beautifulsoup4-4.12.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.31.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "typer" do
    url "https://files.pythonhosted.org/packages/source/t/typer/typer-0.9.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  def install
    virtualenv_install_with_resources
  end

  def post_install
    # Create config directory
    (var/"obsidian-notes-agent").mkpath
  end

  def caveats
    <<~EOS
      To get started with Obsidian Notes Agent:

      1. Configure your API key and vault path:
         notes config

      2. Start using the agent:
         notes chat              # Interactive mode
         notes info              # Check configuration
         notes ingest <url>      # Import content

      Your configuration is stored in:
         ~/.config/obsidian-notes-agent/config.env

      For more information, visit:
         https://github.com/yourusername/obsidian-notes-agent
    EOS
  end

  test do
    assert_match "Obsidian Notes Agent", shell_output("#{bin}/notes --help")
  end
end
