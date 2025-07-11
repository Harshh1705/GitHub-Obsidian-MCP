import os
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()
mcp = FastMCP("Obsidian_MCP")

VAULT_PATH_VALUE = os.getenv("VAULT_PATH")


if VAULT_PATH_VALUE:
    VAULT_PATH = Path(VAULT_PATH_VALUE)

def get_path(note_path:str):
    if not VAULT_PATH:
        return None
    
    full_path = (VAULT_PATH/note_path).resolve()
    
    return full_path

def read_note(full_path:Path):
    if full_path.suffix == ".md" and full_path.is_file():
        return full_path.read_text(encoding="utf-8")
    return None

def append_note(full_path: Path, content_to_append: str, ensure_newline: bool = True) -> bool:
    try:
        if full_path and full_path.is_file() and full_path.suffix.lower() == ".md":
            with full_path.open("a", encoding="utf-8") as f: # 'a' for append mode
                if ensure_newline:
                    current_content = full_path.read_text(encoding="utf-8")
                    if current_content and not current_content.endswith('\n'):
                        f.write('\n')
                f.write(content_to_append)
            return True
        return False
    except Exception as e:
        return False
    
def create_note(relative_path:str, content:str):
    if not VAULT_PATH:
        return None
    if not relative_path.endswith(".md"):
        relative_path += ".md"
    full_path = VAULT_PATH / relative_path
    if not full_path:
        return None
    
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return full_path
    except Exception as e:
        print(f"Error creating markdown note: {e}")
        return None 


@mcp.tool()
def get_obsidian_note(note_path:str):
    """
    Retrieves the content of a specific note from your Obsidian vault.
    The server must be configured with the OBSIDIAN_VAULT_PATH environment variable.
    
    Args:
        note_path (str): The relative path to the note within your vault. 
                         Example: "Meetings/2025-06-07 Project Alpha Sync.md"
                         Example: "Quick Ideas.md" (if in the vault root)
                         
    Returns:
        str: A JSON string containing the note's relative path and its Markdown content.
             If the note is not found or an error occurs, it returns a JSON error message.
             Example success: {"path": "Meetings/MyNote.md", "content": "# Meeting Title\n..."}
             Example error: {"error": "Note not found or could not be read: path/to/note.md"}
    """
    if not VAULT_PATH:
         return json.dumps({"error": "OBSIDIAN_VAULT_PATH not configured on server."})
     
    full_path = get_path(note_path=note_path)
    if not full_path:
        return json.dumps({"error": f"Invalid note path or access denied: {note_path}"})
     
    content = read_note(full_path=full_path)
    
    if content is not None:
        return json.dumps({"path": note_path, "content": content})
    else:
        return json.dumps({"error": f"Note not found or could not be read: {note_path}"})


@mcp.tool()
def create_obsidian_note(relative_path: str, content: str) -> str:
    """
    Creates a new note (or overwrites an existing one) in your Obsidian vault.
    The server must be configured with the OBSIDIAN_VAULT_PATH environment variable.
    If the specified path includes folders that do not exist, they will be created.
    The ".md" extension will be added if not provided.
    
    Args:
        relative_path (str): The desired relative path for the new note within the vault.
                             Example: "Projects/New Feature Ideas.md"
                             Example: "Daily/2025-06-07" (will become "Daily/2025-06-07.md")
        content (str): The Markdown content for the new note.
                         
    Returns:
        str: A JSON string indicating success (including the actual relative path created) or failure.
             Example success: {"message": "Note created/updated successfully.", "path": "Projects/New Feature Ideas.md"}
             Example error: {"error": "Failed to create note at: path/to/note"}
    """
    if not VAULT_PATH:
         return json.dumps({"error": "VAULT_PATH not configured on server."})
    
    create_path = create_note(relative_path=relative_path, content=content) 
    
    if create_path:
        try:
            if VAULT_PATH:
                 created_relative_path_str = str(create_path.relative_to(VAULT_PATH))
            else: 
                 created_relative_path_str = str(create_path) # Fallback, less ideal

            return json.dumps({"message": "Note created/updated successfully.", 
                               "path": created_relative_path_str})
        except ValueError:
            return json.dumps({"error": f"Failed to determine relative path for created note: {str(create_path)}"})

    else:
        return json.dumps({"error": f"Failed to create note at: {relative_path}"})

@mcp.tool()
def append_obsidian_note(note_path: str, content_to_append: str) -> str: # 
    """
    Appends content to an existing note in your Obsidian vault.
    The server must be configured with the OBSIDIAN_VAULT_PATH environment variable.
    If the note does not exist, this operation will fail.
    
    Args:
        note_path (str): The relative path to the existing note within your vault.
                         Example: "Journal/My Thoughts.md"
        content_to_append (str): The Markdown content to append to the end of the note.
                                 A newline will be added before appending if the note doesn't end with one.
                                 
    Returns:
        str: A JSON string indicating success or failure.
             Example success: {"message": "Content appended to 'Journal/My Thoughts.md' successfully."}
             Example error: {"error": "Note not found or is not a file: Journal/My Thoughts.md"}
    """
    if not VAULT_PATH:
         return json.dumps({"error": "VAULT_PATH not configured on server."})
    
    full_path_obj = get_path(note_path)
    if not full_path_obj or not full_path_obj.is_file():
        return json.dumps({"error": f"Note not found or is not a file (cannot append): {note_path}"})
    
    success = append_note(full_path=full_path_obj, content_to_append=content_to_append) 
    
    if success:
        return json.dumps({"message": f"Content appended to '{note_path}' successfully."})
    else:
        return json.dumps({"error": f"Failed to append content to note: {note_path}"})
    
if __name__ == "__main__":
    mcp.run(transport = "stdio")