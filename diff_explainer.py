#!/usr/bin/env python3
"""
Git Diff Explainer - Uses AI to explain git diffs in plain English.

Usage:
    git diff | python diff_explainer.py
    git show abc123 | python diff_explainer.py
    python diff_explainer.py --file my_diff.txt
"""

import sys
import os
import argparse
import json
from typing import Optional, Iterator
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv is required. Install with: pip install python-dotenv")
    sys.exit(1)


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_colored(text: str, color: str = Colors.END) -> None:
    """Print text with color."""
    print(f"{color}{text}{Colors.END}")


def load_api_key() -> str:
    """Load OpenRouter API key from environment."""
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print_colored("\n❌ Error: OPENROUTER_API_KEY not found!", Colors.RED)
        print("1. Get a free API key from https://openrouter.ai/keys")
        print("2. Create .env file with: OPENROUTER_API_KEY=your_key_here")
        sys.exit(1)
    return api_key


def read_diff_input(file_path: Optional[str] = None) -> str:
    """Read git diff from stdin or file."""
    if file_path:
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print_colored(f"❌ Error: File '{file_path}' not found", Colors.RED)
            sys.exit(1)
        except Exception as e:
            print_colored(f"❌ Error reading file: {e}", Colors.RED)
            sys.exit(1)
    else:
        # Read from stdin
        if sys.stdin.isatty():
            print_colored("❌ Error: No input provided", Colors.RED)
            print("\nUsage:")
            print("  git diff | python diff_explainer.py")
            print("  python diff_explainer.py --file diff.txt")
            sys.exit(1)
        
        return sys.stdin.read()


def clean_diff(diff_content: str, max_lines: int = 500) -> str:
    """
    Clean and truncate diff content.
    
    Args:
        diff_content: Raw diff content
        max_lines: Maximum number of lines to keep
        
    Returns:
        Cleaned diff content
    """
    lines = diff_content.strip().split('\n')
    
    # Filter out binary files
    filtered_lines = []
    skip_binary = False
    
    for line in lines:
        if 'Binary files' in line or 'differ' in line:
            skip_binary = True
            continue
        if not skip_binary:
            filtered_lines.append(line)
    
    # Truncate if too long
    if len(filtered_lines) > max_lines:
        filtered_lines = filtered_lines[:max_lines]
        filtered_lines.append(f"\n... (truncated, showing first {max_lines} lines)")
    
    return '\n'.join(filtered_lines)


def create_prompt(diff_content: str) -> str:
    """
    Create the prompt for the AI model.
    
    Args:
        diff_content: The git diff content
        
    Returns:
        Formatted prompt string
    """
    return f"""Explain this git diff in plain English. Focus on:
- What changed (added/removed/modified)
- Why these changes might have been made
- Any potential issues or important notes

Keep it concise and clear. Use bullet points.

Here's the diff:

```
{diff_content}
```"""


def stream_explanation(
    api_key: str,
    prompt: str,
    model: str = "meta-llama/llama-3.2-3b-instruct:free"
) -> Iterator[str]:
    """
    Stream explanation from OpenRouter API.
    
    Args:
        api_key: OpenRouter API key
        prompt: The prompt to send
        model: Model to use (default: free Llama 3.2 3B)
        
    Yields:
        Chunks of text from the streaming response
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-username/diff-explainer",  # Optional
        "X-Title": "Git Diff Explainer",  # Optional
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True,
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    response.read()
                    error_text = response.text
                    raise Exception(f"API error {response.status_code}: {error_text}")
                
                for line in response.iter_lines():
                    line = line.strip()
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
    except httpx.TimeoutException:
        print_colored("\n❌ Error: Request timed out", Colors.RED)
        print("The API took too long to respond. Try again with a smaller diff.")
        sys.exit(1)
    except httpx.ConnectError:
        print_colored("\n❌ Error: Could not connect to OpenRouter", Colors.RED)
        print("Check your internet connection and try again.")
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Error: {e}", Colors.RED)
        sys.exit(1)


def explain_diff(diff_content: str, api_key: str, model: str) -> None:
    """
    Main function to explain a git diff.
    
    Args:
        diff_content: The git diff content
        api_key: OpenRouter API key
        model: Model to use
    """
    # Clean the diff
    cleaned_diff = clean_diff(diff_content)
    
    if not cleaned_diff.strip():
        print_colored("❌ Error: Empty or invalid diff provided", Colors.RED)
        sys.exit(1)
    
    # Show what we're analyzing
    line_count = len(cleaned_diff.split('\n'))
    print_colored(f"\n📊 Analyzing diff ({line_count} lines)...\n", Colors.CYAN)
    
    # Create prompt and stream response
    prompt = create_prompt(cleaned_diff)
    
    print_colored("🤖 AI Explanation:", Colors.BOLD + Colors.GREEN)
    print_colored("─" * 60, Colors.GREEN)
    
    try:
        for chunk in stream_explanation(api_key, prompt, model):
            print(chunk, end='', flush=True)
        print()  # New line at the end
        print_colored("─" * 60, Colors.GREEN)
        
    except KeyboardInterrupt:
        print_colored("\n\n⚠️  Interrupted by user", Colors.YELLOW)
        sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Explain git diffs using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  git diff | python diff_explainer.py
  git show abc123 | python diff_explainer.py  
  python diff_explainer.py --file my_diff.txt
  
Get your free API key at: https://openrouter.ai/keys
        """
    )
    
    parser.add_argument(
        '--file',
        '-f',
        help='Path to file containing git diff',
        type=str
    )
    
    parser.add_argument(
        '--model',
        '-m',
        help='OpenRouter model to use (default: free Llama 3.2 3B)',
        default="meta-llama/llama-3.2-3b-instruct:free",
        type=str
    )
    
    args = parser.parse_args()
    
    # Load API key
    api_key = load_api_key()
    
    # Read diff input
    diff_content = read_diff_input(args.file)
    
    # Explain the diff
    explain_diff(diff_content, api_key, args.model)


if __name__ == "__main__":
    main()