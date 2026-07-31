# Smart Commit Messenger 🚀

An AI-powered Git workflow automation tool that writes your commit messages and pushes your code—so you don't have to!

## What is it?
If you hate breaking your coding flow to think of a Git commit message, this tool is for you. Instead of manually typing `git add`, struggling to think of a message, running `git commit`, and finally `git push`, you just run **one command**: `smartcommit`. 

The tool uses local AI to analyze your code changes (diffs), generates a perfect Conventional Commit message (e.g., `feat: added login page`), asks for your confirmation, and handles the rest of the Git workflow automatically. It even logs all your commits locally to a CSV!

## Features
- 🧠 **Local AI Powered**: Uses [Ollama](https://ollama.com/) to keep your code private while generating intelligent messages.
- ⚡ **One-Command Workflow**: Replaces multiple manual Git commands with a single command.
- 🚀 **Auto-Detects New Files**: Automatically runs `git add .` if new untracked files are created.
- 🔗 **Auto-Sets Upstream**: Automatically handles first-time branch pushes (`git push -u origin <branch>`).
- ☁️ **Auto-Push**: Commits and automatically pushes your code to your GitHub branch.
- 📜 **History Tracking**: Saves every commit to a local `commit_history.csv` for easy reference.

## Prerequisites
- [Git](https://git-scm.com/) installed.
- [Python 3](https://www.python.org/) installed.
- [Ollama](https://ollama.com/) installed and running locally with the `qwen2.5-coder:3b` model.

## Installation & Setup
1. Clone this repository to your computer.
2. Make sure you have the required Python packages installed (you can use `pip install requests python-dotenv`).
3. (Optional but recommended) Add the directory containing `smartcommit.bat` to your Windows System `PATH`. This allows you to open any project folder in your terminal and simply type `smartcommit`!

## Using Other AI Models (OpenAI, Gemini, etc.)
If you don't have Ollama installed or prefer to use a cloud LLM like OpenAI, you can easily change the API request in `Logic/ai_utils.py`. 

Open `Logic/ai_utils.py` and replace the Ollama request:

**Old Code (Ollama):**
```python
            response = requests.post('http://localhost:11434/api/generate', json={
                "model": "qwen2.5-coder:3b",
                "prompt": f'Generate a short, one-line commit message for this git diff. '
                          f'Use Conventional Commits format (feat:, fix:, docs:, etc.). '
                          f'Only output the message, no extra text.\n\nDiff:\n{diff_text}',
                "stream": True,
                "keep_alive": -1,
                "options": {
                    "num_predict": 50
                }
            }, stream=True, timeout=30)
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
1. Make some changes to your code (or create new files).
2. Open your terminal in your project directory.
3. Type the command:
   ```bash
   smartcommit
   ```
4. The AI will scan your code and stream a suggested message. Type `y` to accept it! The tool will commit the code and automatically push it to GitHub.

*(If you want to skip the `y/n` confirmation and force the commit, you can run `smartcommit -y`)*

---

## 🚀 Feature Roadmap
- [x] **Auto-Add Untracked Files**: Automatically detecting and staging brand-new files.
- [x] **Auto-Fix First Time Pushes**: Automatically detecting first-time branch pushes and linking upstream (`-u origin <branch>`).
- [ ] **Multiple AI Choices**: Generating 3 different commit message options and letting you choose your favorite (1, 2, or 3).
- [ ] **Custom AI Models**: Allowing you to easily switch AI models (like Llama 3) via the `.env` config file.
- [ ] **Diff Context Improvements**: Sending the AI file names alongside the diff so it never loses context on massive code changes.
