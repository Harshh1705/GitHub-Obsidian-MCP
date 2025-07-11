# My Custom MCP Servers for Claude Desktop

This repository contains two Model Context Protocol (MCP) servers designed for use with Claude Desktop:

1. **`Github_Server.py`**: Provides tools to interact with the GitHub API.  
2. **`Obsidian_Server.py`**: Provides tools to interact with a local Obsidian vault.

## Prerequisites

1. **Python:** Ensure you have Python 3.8+ installed and available in your system's PATH.
2. **Claude Desktop:** You must have the [Claude Desktop application](https://claude.ai/download) installed.
3. **Python Packages:** It's highly recommended to use a virtual environment.

    ```bash
    # Create and activate a virtual environment (e.g., venv)
    python -m venv .venv
    # On Windows: .venv\Scripts\activate
    # On macOS/Linux: source .venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
    ```

4. **API Keys & Paths:**
    - A **GitHub Personal Access Token (PAT)** with `repo` scope.
    - The absolute path to your **Obsidian Vault** directory.

## Setup Instructions

To use these servers with Claude Desktop, you must create a local configuration file that points to these scripts and provides your personal paths and API keys.

**This configuration file contains secrets and MUST NOT be committed to version control.**

### Step 1: Locate Your Claude Configuration Directory

Find the Claude Desktop configuration directory on your system:

- **Windows:** `%APPDATA%\Claude\` (typically resolves to `C:\Users\YourUsername\AppData\Roaming\Claude\`)
- **macOS:** `~/Library/Application Support/Claude/`

### Step 2: Create `claude_desktop_config.json`

1. Inside the Claude configuration directory, create a file named `claude_desktop_config.json` if it doesn't already exist.
2. Copy the entire content of the `config.template.json` file from this repository.
3. Paste the content into your new `claude_desktop_config.json` file.

### Step 3: Replace All Placeholders in Your Local File

Edit your local `claude_desktop_config.json` and replace all placeholders (`<...>`) with your actual information.

**Example Placeholders:**

- **`<PATH_TO_YOUR_PYTHON_EXECUTABLE>`**:
    - Get this by activating your virtual environment and running:
      - `where python` (Windows)
      - `which python` (macOS/Linux)
    - Example (Windows): `"C:\\Users\\Harsh\\projects\\your-mcp-project\\.venv\\Scripts\\python.exe"`

- **`<ABSOLUTE_PATH_TO_YOUR_PROJECT_FOLDER>`**:
    - Example (Windows): `"C:\\Users\\Harsh\\projects\\your-mcp-project"`
    - Use **double backslashes (`\\`)** in JSON.

- **`"YOUR_GITHUB_PERSONAL_ACCESS_TOKEN_HERE"`**:
    - Replace this with your actual GitHub PAT.
    - Example: `"ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"`

- **`<ABSOLUTE_PATH_TO_YOUR_OBSIDIAN_VAULT>`**:
    - Example (Windows): `"C:\\Users\\Harsh\\Documents\\MyObsidianVault"`

### Step 4: Save and Restart

1. Save changes to `claude_desktop_config.json`.
2. **Completely quit and restart Claude Desktop** to load the new server configurations.
3. If successful, both servers will appear in the "Search and tools" section in Claude chat.

### Example of a Final, Filled-Out `claude_desktop_config.json` (DO NOT COMMIT THIS)

```json
{
  "mcpServers": {
    "MyGitHubServer": {
      "command": "C:\\Users\\Harsh\\projects\\your-mcp-project\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\Harsh\\projects\\your-mcp-project\\Github_Server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "PYTHONUNBUFFERED": "1"
      },
      "cwd": "C:\\Users\\Harsh\\projects\\your-mcp-project"
    },
    "MyObsidianServer": {
      "command": "C:\\Users\\Harsh\\projects\\your-mcp-project\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\Harsh\\projects\\your-mcp-project\\Obsidian_Server.py"
      ],
      "env": {
        "VAULT_PATH": "C:\\Users\\Harsh\\Documents\\MyObsidianVault",
        "PYTHONUNBUFFERED": "1"
      },
      "cwd": "C:\\Users\\Harsh\\projects\\your-mcp-project"
    }
  }
}
```