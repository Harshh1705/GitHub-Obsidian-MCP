import os
import requests
import json
import base64
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Github_MCP")

# --- Helper Class for GitHub API Interaction --- as good as class github from toollake/code/github 
class GitHubHelper:
    """
    This class contains :
    1. constructor to intialise owner, repo and github_token ( passed as env )
    2. make request function to make a request to github with args as method and endpoint and uses a common url with ower, repo and endpoint 
    """
    def __init__(self, owner: str, repo: str, github_token: str):
        self.owner = owner
        self.repo = repo
        self.github_token = github_token
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28" # Recommended by GitHub
        }
        print(f"GitHubHelper initialized for repository: {owner}/{repo}")

    def _make_github_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Internal helper to make requests to the GitHub API.
        """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/{endpoint}"
        print(f"Making GitHub API request: {method.upper()} {url}")
        try:
            response = requests.request(method, url, headers=self.headers, timeout=20, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as http_err:
            print(f"GitHub API HTTP error: {http_err}. Response status: {http_err.response.status_code}. Response text: {http_err.response.text if http_err.response else 'No response body'}")
            raise # Re-raise the exception to be handled by the calling tool function
        except requests.exceptions.RequestException as req_err:
            print(f"GitHub API Request (network/connection) error: {req_err}")
            raise
        except Exception as e:
            print(f"Unexpected error in _make_github_request: {e}")
            raise

    def get_last_merged_pr_details(self) -> Optional[Dict[str, Any]]:
        """
        Fetches and returns details of the last merged pull request.
        Returns None if no merged PR is found, or a dictionary with error details on failure.
        """
        try:
            response = self._make_github_request("GET", "pulls?state=closed&sort=updated&direction=desc&per_page=10")
            pull_requests = response.json()

            for pr in pull_requests:
                if pr.get("merged_at"): # Indicates the PR was merged
                    
                    # Return a curated set of information
                    return {
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "url": pr.get("html_url"),
                        "merged_at": pr.get("merged_at"),
                        "merged_by": pr.get("merged_by", {}).get("login") if pr.get("merged_by") else None,
                        "author": pr.get("user", {}).get("login") if pr.get("user") else None,
                        "body_summary": (pr.get("body", "")[:200] + "...") if pr.get("body") and len(pr.get("body", "")) > 200 else pr.get("body", ""),
                        "head_commit_sha": pr.get("head", {}).get("sha") if pr.get("head") else None,
                        "base_branch": pr.get("base", {}).get("ref") if pr.get("base") else None,
                    }
            print(f"No merged PRs found in the last 10 closed PRs for {self.owner}/{self.repo}.")
            return None # Explicitly return None if no merged PR is found
        except Exception as e:
            
            print(f"Error processing PR data in get_last_merged_pr_details for {self.owner}/{self.repo}: {e}")
            # Return a dictionary with an error key, as the tool expects a JSON stringizable dict
            return {"error_message": f"Failed to retrieve or process last merged PR details: {str(e)}"}
    
    def get_dir_content(self, dir_path:str = ""):
        endpoint = f"contents/{dir_path}"
        try:
            response = self._make_github_request("GET", endpoint)
            items = response.json()
            dir_content = []
            for item in items:
                dir_content.append({
                "name": item.get("name"),
                "path": item.get("path"),
                "type": item.get("type"), # 'file', 'dir', 'symlink', etc.
                "size": item.get("size"),
                "sha": item.get("sha"),
                "html_url": item.get("html_url"),
                "download_url": item.get("download_url") 
                })
            return dir_content
        except requests.exceptions.HTTPError as e:
            return {"error_message": f"Directory or path not found: {dir_path} in {self.owner}/{self.repo}"}
            
    def get_file_content(self, file_path:str):
        endpoint = f"contents/{file_path}"
        
        try:
            response = self._make_github_request("GET", endpoint=endpoint)
            file_data = response.json()
            
            content_b64 = file_data.get("content")
            decoded_content = ""
            encoding = file_data.get("encoding")
            
            if content_b64 and encoding == "base64":
                try:
                    decoded_content = base64.b64decode(content_b64).decode('utf-8')
                except Exception as decode_err:
                    decoded_content = "Error: Could not decode content."
                    encoding = "error_decoding_base64"
            elif file_data.get("download_url"):
                try:
                    raw_response = requests.get(file_data["download_url"], timeout=30)
                    decoded_content= raw_response.text
                    encoding = raw_response.encoding or "utf-8"           
                except Exception as dl_err:
                    decoded_content = "Error: Could not download content."
                    encoding = "error_downloading"
            
            return {
            "name": file_data.get("name"),
            "path": file_data.get("path"),
            "sha": file_data.get("sha"),
            "size": file_data.get("size"),
            "encoding": encoding,
            "content": decoded_content,
            "html_url": file_data.get("html_url"),
            "download_url": file_data.get("download_url")
            }
        except requests.exceptions.HTTPError as e:
            return {"error_message": f"content not found: {file_path} in {self.owner}/{self.repo}"}
        
        
# --- MCP Tool Definition ---
@mcp.tool()
def get_github_last_merged_pr(owner: str, repo: str) -> str:
    """
    Retrieves details of the most recently merged Pull Request for a specified GitHub repository.
    This tool requires the GITHUB_TOKEN environment variable to be set for authentication,
    especially for private repositories or to avoid rate limits.
    
    Args:
        owner (str): The owner (username or organization) of the GitHub repository. 
                     Example: "modelcontextprotocol"
        repo (str): The name of the GitHub repository. 
                    Example: "specification"
                    
    Returns:
        str: A JSON string containing details of the last merged PR.
             If no merged PRs are found, it returns a JSON message indicating so.
             If an error occurs (e.g., token missing, API error), it returns a JSON error message.
    """
    print(f"Tool 'get_github_last_merged_pr' called for repo: {owner}/{repo}")

    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        print("CRITICAL: GITHUB_TOKEN environment variable is not set. This tool cannot function.")
        # Return a JSON string indicating the error
        return json.dumps({
            "error": "ConfigurationError",
            "error_message": "GITHUB_TOKEN environment variable not set on the server. Please ensure it's configured for the MCP server process (e.g., in Claude Desktop's mcpServers config)."
        })

    try:
        # Instantiate the helper class for this specific request
        gh_helper = GitHubHelper(owner=owner, repo=repo, github_token=github_token)
        pr_data = gh_helper.get_last_merged_pr_details()

        if pr_data is None: # No merged PR found
            return json.dumps({"message": f"No recently merged PRs found for {owner}/{repo}."})
        elif "error_message" in pr_data: # An error occurred within the helper
             return json.dumps(pr_data) # pr_data already contains the error dict
        else: 
            return json.dumps(pr_data, indent=2) # Pretty print JSON for readability

    except Exception as e:
        
        print(f"Unexpected tool error in 'get_github_last_merged_pr' for {owner}/{repo}: {e}")
        return json.dumps({
            "error": "ToolExecutionError",
            "error_message": f"An unexpected error occurred in the tool: {str(e)}",
            "details": {"owner": owner, "repo": repo}
        })


@mcp.tool()
def get_repo_contents(owner:str, repo:str, path:str = ""):
    """
    Lists files and directories at a given path within a specified GitHub repository.
    If the path points to a file, it may return details about that file instead (behavior of GitHub API).
    Requires GITHUB_TOKEN environment variable for authentication.

    Args:
        owner (str): The owner/organization of the GitHub repository. Example: "octocat"
        repo (str): The name of the GitHub repository. Example: "Spoon-Knife"
        path (str, optional): The path within the repository to list. Defaults to the root directory ("").
                             Example: "src/components", "README.md"
    Returns:
        str: A JSON string. If path is a directory, it's a list of objects, each representing a file or
             directory with keys like "name", "path", "type", "size", "sha", "html_url", "download_url".
             If path is a file, it may return a single object with file details (potentially including
             base64 encoded content if small).
             Returns a JSON error object on failure.
             Example (directory): [{"name": "file.py", "type": "file", ...}, {"name": "subdir", "type": "dir", ...}]
             Example (error): {"error": "...", "details": "..."}
    """
    
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        return json.dumps({
            "error": "ConfigurationError",
            "error_message": "GITHUB_TOKEN environment variable not set on the server. Please ensure it's configured for the MCP server process (e.g., in Claude Desktop's mcpServers config)."
        })
    
    gh_helper = GitHubHelper(owner=owner, repo=repo, github_token=github_token)
    contents = gh_helper.get_dir_content(path) 
    # if contents is None:
    #     return json.dumps({"error": "NotFound", "error_message": f"Path '{path}' not found in {owner}/{repo}."})
    return json.dumps(contents, indent=2)


@mcp.tool()
def get_file_contents(owner:str, repo:str, path:str):
    """
    Retrieves the decoded content and details of a specific file from a GitHub repository.
    Requires GITHUB_TOKEN environment variable for authentication.

    Args:
        owner (str): The owner/organization of the GitHub repository.
        repo (str): The name of the GitHub repository.
        file_path (str): The full path to the file within the repository. Example: "src/main.py", "README.md"
       
    Returns:
        str: A JSON string containing an object with keys like "name", "path", "size", "encoding", 
             and "content" (the decoded file content).
             Returns a JSON error object on failure or if the path is not a file.
             Example (success): {"name": "main.py", "path": "src/main.py", "content": "print('hello')", ...}
             Example (error): {"error": "NotFound", "error_message": "File 'path/to/file.ext' not found."}
    """
    
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        return json.dumps({
            "error": "ConfigurationError",
            "error_message": "GITHUB_TOKEN environment variable not set on the server. Please ensure it's configured for the MCP server process (e.g., in Claude Desktop's mcpServers config)."
        })
    
    gh_helper = GitHubHelper(owner=owner, repo=repo, github_token=github_token)
    
    file_content = gh_helper.get_file_content(path)
    
    if file_content is None: 
        return json.dumps({"error": "NotFound", "error_message": f"File '{path}' not found in {owner}/{repo}."})
    if "error_message" in file_content: 
        return json.dumps(file_content)
    
    return json.dumps(file_content, indent=2)
# --- Main Execution Block ---
if __name__ == "__main__":
    # This block is executed when you run `python server.py` directly

    print("-----------------------------------------------------")
    print("GitHub Last PR MCP Server attempting to start...")
    print("-----------------------------------------------------")

    if not os.getenv("GITHUB_TOKEN"):
        print("WARNING: GITHUB_TOKEN environment variable is NOT set.")
        print("The 'get_github_last_merged_pr' tool will fail until GITHUB_TOKEN is provided to this server's environment.")
    else:
        print("GITHUB_TOKEN environment variable is set.")

    mcp.run(transport='stdio')

    print("-----------------------------------------------------")
    print("GitHub Last PR MCP Server has shut down.")
    print("-----------------------------------------------------")