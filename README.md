# Smart Commit Messenger 🚀

An AI-powered Git workflow automation tool that automatically generates Conventional Commit messages from your code changes, commits them, and pushes to GitHub—so you don't have to break your flow!

---

## 🌟 Key Features

- 🧠 **Local & Private AI**: Runs 100% locally using [Ollama](https://ollama.com/) (`qwen2.5-coder`), keeping your code completely private.
- ⚡ **One-Command Workflow**: Replaces `git add`, `git commit`, and `git push` with a single command: `smartcommit`.
- 📁 **Auto-Detects Untracked Files**: Automatically stages brand-new files with `git add .`.
- 🔗 **Auto Upstream Setup**: Automatically links new local branches to GitHub on first push (`git push -u origin <branch>`).
- 📜 **Commit Logging**: Saves all commit history locally into `commit_history.csv`.
- 🛠️ **Customizable**: Supports custom Ollama models and cloud APIs (OpenAI, Gemini, etc.).

---

## 📋 Prerequisites (What You Need to Install First)

Before setting up the project, make sure you have the following installed on your computer:

1. **Git**: [Download Git](https://git-scm.com/downloads)
2. **Python 3.8+**: [Download Python](https://www.python.org/downloads/)  
   *(⚠️ **Important during Windows installation**: Check the box **"Add Python to PATH"**!)*
3. **Ollama**: [Download Ollama](https://ollama.com/download)  
   *(Ollama allows you to run AI models locally on your GPU/CPU).*

---

## ⚙️ Step-by-Step Setup Guide

Follow these steps to set up Smart Commit Messenger on your machine:

### Step 1: Download & Run the Local AI Model
Open your terminal (PowerShell / Command Prompt / Terminal) and run:

```bash
ollama pull qwen2.5-coder:7b
```
*(If your computer has lower RAM/VRAM, you can pull the lightweight 3B model instead: `ollama pull qwen2.5-coder:3b`)*

---

### Step 2: Clone the Repository
Clone this repository to a folder on your computer:

```bash
git clone https://github.com/anikdey72196-ops/Smart-commit-mesenger.git
cd "Smart commit mesenger"
```

---

### Step 3: Set Up Python Virtual Environment
Create and activate a virtual environment, then install required packages:

#### Windows (Command Prompt / PowerShell):
```bash
python -m venv venv
.\venv\Scripts\activate
pip install requests python-dotenv
```

#### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install requests python-dotenv
```

---

### Step 4: Create Environment File (`.env`)
Copy `.env.example` to create `.env`:

**Windows:**
```cmd
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Ensure `.env` contains:
```env
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_HOST=http://localhost:11434
```
*(If you pulled `qwen2.5-coder:3b` in Step 1, update `OLLAMA_MODEL=qwen2.5-coder:3b` inside `.env`).*

---

## 🌐 Manual Setup: Access `smartcommit` from ANY Folder

To use `smartcommit` from any project folder in your terminal, set up the command shortcut below for your operating system:

### Option A: Windows (System PATH - Recommended)
1. Press `Win + R`, type `sysdm.cpl`, and press **Enter**.
2. Click the **Advanced** tab -> click **Environment Variables**.
3. Under **User variables**, select `Path` and click **Edit**.
4. Click **New** and paste the **full folder path** where `Smart commit mesenger` is located (where `smartcommit.bat` lives).
   *Example: `C:\Users\YourName\Documents\Smart commit mesenger`*
5. Click **OK** on all dialogs.
6. Restart your open terminal windows. You can now type `smartcommit` in **any** git directory!

### Option B: Windows (PowerShell Profile)
Open PowerShell and edit your profile:
```powershell
notepad $PROFILE
```
Add the following line (replace with your actual folder path):
```powershell
function smartcommit { & "C:\path\to\Smart commit mesenger\venv\Scripts\python.exe" "C:\path\to\Smart commit mesenger\Logic\code.py" $args }
```

### Option C: macOS / Linux (Bash / Zsh Alias)
Add this alias to your shell config file (`~/.zshrc` or `~/.bashrc`):
```bash
alias smartcommit='/path/to/Smart commit mesenger/venv/bin/python /path/to/Smart commit mesenger/Logic/code.py'
```
Then run `source ~/.zshrc` or `source ~/.bashrc`.

---

## 🎯 How to Use

1. Open your terminal in **any** project directory managed by Git.
2. Make some changes to your code or create new files.
3. Run:
   ```bash
   smartcommit
   ```
4. The local AI will analyze your diff and stream a suggested commit message:
   ```text
   Changes detected:
   1 file changed, 5 insertions(+)

   Suggested message: feat(auth): add JWT token validation for user login
   Use this message? (y/n):
   ```
5. Type `y` and hit Enter! The tool will:
   - Stage untracked files automatically (`git add .`)
   - Commit changes with the AI message
   - Push to your active GitHub branch
   - Log the entry in `commit_history.csv`

### Useful Flags
- `smartcommit -y` : Skip confirmation and commit/push immediately.
- `smartcommit --dry-run` : Show generated message without committing or pushing.

---

## ☁️ Using OpenAI / Cloud APIs Instead of Ollama

If you don't want to run Ollama locally and prefer cloud AI APIs (like OpenAI GPT-4o), edit `Logic/ai_utils.py` and replace the Ollama request with:

```python
import os, requests

def generate_commit_message(diff_text):
    api_key = os.getenv("OPENAI_API_KEY")
    response = requests.post("https://api.openai.com/v1/chat/completions", headers={
        "Authorization": f"Bearer {api_key}"
    }, json={
        "model": "gpt-4o-mini",
        "messages": [{
            "role": "user",
            "content": f"Generate a short, one-line Conventional Commit message for this diff:\n\n{diff_text}"
        }]
    })
    return response.json()["choices"][0]["message"]["content"].strip()
```

Add `OPENAI_API_KEY=your_key_here` into your `.env` file.

---

## ❓ Troubleshooting

- **`smartcommit` is not recognized as a command**:
  Ensure you added the `Smart commit mesenger` directory to your system PATH or shell profile, and restart your terminal.
- **Connection refused / Ollama busy**:
  Make sure Ollama is running in your system tray or run `ollama serve` in a separate terminal.
- **Not a git repository**:
  Run `git init` first in the project directory where you want to commit.

---

## 📜 License
MIT License. Feel free to fork, customize, and share!
