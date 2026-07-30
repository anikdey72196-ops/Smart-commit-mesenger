# Smart Commit Messenger 🚀

An AI-powered Git workflow automation tool that writes your commit messages and pushes your code—so you don't have to!

## What is it?
If you hate breaking your coding flow to think of a Git commit message, this tool is for you. Instead of manually typing `git add`, struggling to think of a message, running `git commit`, and finally `git push`, you just run **one command**: `smartcommit`. 

The tool uses local AI to analyze your code changes (diffs), generates a perfect Conventional Commit message (e.g., `feat: added login page`), asks for your confirmation, and handles the rest of the Git workflow automatically. It even logs all your commits locally to a CSV!

## Features
- 🧠 **Local AI Powered**: Uses [Ollama](https://ollama.com/) to keep your code private while generating intelligent messages.
- ⚡ **One-Command Workflow**: Replaces multiple manual Git commands with a single command.
- ☁️ **Auto-Push**: Commits and automatically pushes your code to your GitHub branch.
- 📜 **History Tracking**: Saves every commit to a local `commit_history.csv` for easy reference.

## Prerequisites
- [Git](https://git-scm.com/) installed.
- [Python 3](https://www.python.org/) installed.
- [Ollama](https://ollama.com/) installed and running locally with the `qwen2.5-coder:7b` model.

## Installation & Setup
1. Clone this repository to your computer.
2. Make sure you have the required Python packages installed (you can use `pip install requests python-dotenv`).
3. (Optional but recommended) Add the directory containing `smartcommit.bat` to your Windows System `PATH`. This allows you to open any project folder in your terminal and simply type `smartcommit`!

## Using Other AI Models (OpenAI, Gemini, etc.)
If you don't have Ollama installed or prefer to use a cloud LLM like OpenAI, you can easily change the API request in `code.py`. 

Open `code.py` and look for the API request around line 90. Replace the Ollama request with your preferred API:

**Old Code (Ollama):**
```python
            response = requests.post('http://localhost:11434/api/generate', json={
                "model": "qwen2.5-coder:7b",
                "prompt": f'Generate a short, one-line commit message for this git diff. '
                          f'Use Conventional Commits format (feat:, fix:, docs:, etc.). '
                          f'Only output the message, no extra text.\n\nDiff:\n{diff_text}',
                "stream": False
            })
            response.raise_for_status()
            commit_msg = response.json().get('response', '').strip()
```

**New Code (Example using OpenAI):**
```python
            # Ensure you have your API key set in your .env file
            response = requests.post('https://api.openai.com/v1/chat/completions', headers={
                "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"
            }, json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": f'Generate a short, one-line commit message for this git diff. Use Conventional Commits format. Only output the message, no extra text.\n\nDiff:\n{diff_text}'}]
            })
            response.raise_for_status()
            commit_msg = response.json()['choices'][0]['message']['content'].strip()
```

## How to Use
1. Make some changes to your code.
2. Open your terminal in your project directory.
3. Type the command:
   ```bash
   smartcommit
   ```
4. The AI will scan your code and suggest a message. Type `y` to accept it! The tool will commit the code and automatically push it to GitHub.

*(If you want to skip the `y/n` confirmation and force the commit, you can run `smartcommit -y`)*

---

## Important Notes & Current Limitations
Because this tool is currently in development, there are a few things it doesn't cover yet:

* **Brand-New Files (Untracked):** If you create a brand-new file, Git hides it by default. You must run `git add .` once before running `smartcommit` so the AI can see the new file. (If you are just editing existing files, you don't need to do this).
* **First-Time Repo Pushes:** If you are pushing a brand-new repository to GitHub for the very first time, the auto-push will fail because the branch isn't linked yet. You will need to manually run `git push -u origin main` once to link them.

## 🚀 Upcoming Features (What's Next?)
We are actively working on improving the tool! Here is what we will be upgrading next:
- [ ] **Auto-Add Untracked Files**: Automatically detecting and prompting you to add brand-new files so you never have to run `git add .` manually.
- [ ] **Auto-Fix First Time Pushes**: Automatically setting the upstream branch on new repositories.
- [ ] **Multiple AI Choices**: Generating 3 different commit message options and letting you choose your favorite (1, 2, or 3).
- [ ] **Custom AI Models**: Allowing you to easily switch AI models (like Llama 3) via the `.env` config file.
- [ ] **Diff Context Improvements**: Sending the AI file names alongside the diff so it never loses context on massive code changes.
