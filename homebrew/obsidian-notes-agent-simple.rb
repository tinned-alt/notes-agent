class ObsidianNotesAgent < Formula
  include Language::Python::Virtualenv

  desc "AI-powered agent for managing Obsidian notes with Claude"
  homepage "https://github.com/yourusername/obsidian-notes-agent"
  # For local testing, use:
  # url "file:///path/to/notes-agent/dist/obsidian_notes_agent-0.1.0.tar.gz"
  # For GitHub release, use:
  url "https://github.com/yourusername/obsidian-notes-agent/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "YOUR_SHA256_HERE"
  license "MIT"
  head "https://github.com/yourusername/obsidian-notes-agent.git", branch: "main"

  depends_on "python@3.12"

  def install
    # Create virtualenv and install package with all dependencies
    virtualenv_install_with_resources

    # Generate shell completions if available
    # generate_completions_from_executable(bin/"notes", shells: [:bash, :zsh])
  end

  def post_install
    # Create config directory with proper permissions
    config_dir = Pathname.new(Dir.home) / ".config" / "obsidian-notes-agent"
    config_dir.mkpath
    config_dir.chmod 0700
  end

  def caveats
    <<~EOS
      ╭──────────────────────────────────────────────────────────╮
      │  Obsidian Notes Agent installed successfully!            │
      ╰──────────────────────────────────────────────────────────╯

      🔧 First-time setup:
         Run this command to configure your API key and vault:
           notes config

      📖 Usage:
         notes chat              Interactive chat with your notes
         notes ingest <url>      Import content from URL/file
         notes query "question"  Ask a single question
         notes info              View current configuration
         notes reindex           Rebuild search index

      🔑 Get your Anthropic API key:
         https://console.anthropic.com/

      📁 Configuration stored at:
         ~/.config/obsidian-notes-agent/config.env

      🔒 Security:
         Your API key is stored locally with 0600 permissions
         and is never included in version control.

      📚 Full documentation:
         https://github.com/yourusername/obsidian-notes-agent
    EOS
  end

  test do
    # Test that the command is available and shows help
    assert_match "Obsidian Notes Agent", shell_output("#{bin}/notes --help")
  end
end
