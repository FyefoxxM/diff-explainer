# Git Diff Explainer

Uses AI to explain git diffs in plain English with streaming responses.

## Why This Exists

Ever look at a git diff and think "what the hell happened here?" This tool sends your diff to an AI model and gets back a clear explanation of what changed and why it might matter.

Perfect for:
- Code reviews
- Understanding someone else's changes
- Remembering what you did last week
- Learning from complex diffs

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install httpx python-dotenv
```

### 2. Get an OpenRouter API Key

1. Go to [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Sign up (it's free)
3. Create a new API key
4. Copy the key

### 3. Configure Your API Key

Create a `.env` file in this directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
OPENROUTER_API_KEY=sk-or-v1-abc123...
```

**Or** set it as an environment variable:
```bash
export OPENROUTER_API_KEY=sk-or-v1-abc123...
```

## Usage

### Explain Uncommitted Changes
```bash
git diff | python diff_explainer.py
```

### Explain a Specific Commit
```bash
git show abc123 | python diff_explainer.py
```

### Explain Changes Between Branches
```bash
git diff main..feature-branch | python diff_explainer.py
```

### Explain a Diff File
```bash
python diff_explainer.py --file my_diff.txt
```

### Use a Different Model
```bash
# Use a paid model (faster, better quality)
git diff | python diff_explainer.py --model meta-llama/llama-3.1-8b-instruct

# Default is the free tier model
# meta-llama/llama-3.2-3b-instruct:free
```

## Example Output

```
📊 Analyzing diff (47 lines)...

🤖 AI Explanation:
────────────────────────────────────────────────────────────
**Changes Made:**

• Added new `validate_input()` function to check user input before processing
• Modified `process_data()` to use the new validation
• Removed old error handling code that was duplicated
• Updated imports to include the new validation module

**Why These Changes:**

• Centralized validation logic - easier to maintain
• Better error messages for users
• Reduced code duplication
• More robust input handling

**Notes:**

• The validation might be stricter than before - check edge cases
• Error messages changed - update any documentation
────────────────────────────────────────────────────────────
```

## How It Works

1. Reads your git diff (from stdin or file)
2. Cleans it up (removes binary files, truncates if too long)
3. Sends it to OpenRouter's API with streaming enabled
4. Displays the explanation as it's generated (token by token)
5. Handles errors gracefully

## Cost

**Free tier:** Uses `meta-llama/llama-3.2-3b-instruct:free`
- 20 requests per minute
- 200 requests per day
- Perfect for personal use

**Paid models:** Start at ~$0.05 per million tokens
- For a typical diff (500 lines), expect to pay ~$0.01-0.02
- Way cheaper than ChatGPT Pro

## Limitations

- **Max diff size:** 500 lines (truncates longer diffs)
- **Binary files:** Automatically filtered out
- **Rate limits:** Free tier has daily limits
- **Network required:** Needs internet connection
- **AI quality:** Free models are good but not perfect

## Troubleshooting

### "OPENROUTER_API_KEY not found"
Create a `.env` file with your API key or set it as an environment variable.

### "API error 429: Rate limit exceeded"
You hit the free tier limit. Wait a bit or upgrade your OpenRouter account.

### "Request timed out"
Your diff might be too large. Try a smaller commit or specific files:
```bash
git diff path/to/file.py | python diff_explainer.py
```

### Empty or weird output
The AI model might be struggling. Try:
- Using a different model with `--model`
- Reducing the diff size
- Making sure your diff is valid

## What I Learned Building This

- OpenRouter's streaming API is *fast* - watching explanations appear token-by-token is satisfying
- httpx handles SSE streams way better than requests
- Free AI models are surprisingly good for this use case
- Git diffs need cleaning (binary files, truncation) before sending to AI
- Color coding terminal output makes a huge difference in UX

## Stats

- **Lines of code:** ~290
- **Time to build:** ~6 hours
- **Dependencies:** 2 (httpx, python-dotenv)
- **Cost per use:** $0.00 (free tier) to $0.02 (paid models)

## Future Ideas (v2)

- Support for multiple files at once
- Cache explanations (don't re-explain the same diff)
- Commit message suggestions based on diff
- Integration with git as a custom command
- Web UI for non-terminal users

## License

Do whatever you want with this code. MIT License or public domain, your choice.

## Questions?

This is part of my [30 for 30 challenge]([https://jdookeran.medium.com/build-30-for-30-day-02-git-diff-explainer-115cbe62329e]) - building 30 tools in 30 days.

Found a bug? Have a suggestion? Open an issue or just yell at me on Twitter.
