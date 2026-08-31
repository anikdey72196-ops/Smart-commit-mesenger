# Standard Library Substitution Log (STDLIB.md)

This project strictly adheres to the **Zero Dependency** constraint of the *Zero Dependency 2026 Hackathon*. It relies **100% on the Python Standard Library** with zero runtime third-party packages installed (`pip install` packages = 0).

Below is the complete log documenting what packages developers normally use for this type of application, and the standard-library functionality used instead to build **Smart Commit Messenger**.

---

## 📋 Package Substitution Log

| # | Package Normally Used | Standard Library Replacement Used | Architectural Implementation Details |
| :-: | :--- | :--- | :--- |
| **1** | `requests` / `httpx` | `urllib.request`, `urllib.error` | Built a zero-dependency HTTP client using `urllib.request.Request` and `urllib.request.urlopen` with strict socket timeouts (`timeout=35`) and JSON payload encoding (`json.dumps().encode('utf-8')`). |
| **2** | `python-dotenv` | `os`, `os.path`, `open()` | Handled environment variable parsing in `Logic/config.py` by reading `.env` line-by-line, filtering comments (`#`), splitting on `=`, and populating `os.environ`. |
| **3** | `GitPython` / `git` wrapper | `subprocess.run` | Executed native Git CLI commands (`git diff`, `git rev-parse`, `git ls-files`, `git add`, `git commit`, `git push`) with `capture_output=True`, `text=True`, and UTF-8 encoding. |
| **4** | `rich` / `colorama` | Native ANSI Escape Sequences (`\033[...]`) | Implemented terminal colors (Cyan, Green, Yellow, Red, Magenta, Bold) using raw ANSI escape codes in `Logic/ui_utils.py` without requiring external terminal formatting libraries. |
| **5** | `halo` / `yaspin` | `threading.Thread`, `sys.stdout`, `time` | Built a non-blocking animated braille spinner (`⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`) running on a background daemon thread (`threading.Thread(daemon=True)`). |
| **6** | `click` / `typer` | `argparse` | Built command-line flag parsing (`-y` / `--yes`, `--dry-run`, `-h` / `--help`) using standard library `argparse.ArgumentParser`. |
| **7** | `pandas` / `csv-writer` | `csv`, `datetime` | Managed local commit logging into `commit_history.csv` using Python's built-in `csv.writer` and ISO 8601 formatting (`datetime.datetime.now().strftime(...)`). |
| **8** | `pytest` | `unittest`, `unittest.mock` | Implemented test suites and subprocess/HTTP mocks using standard library `unittest.TestCase` and `unittest.mock.patch`. |
| **9** | `pydantic` / `json-parser` | `json`, `re` | Parsed structured LLM JSON responses with defensive fallback regex parsing (`re.sub`, `re.finditer`) to handle markdown backticks (` ```json `) and numbered lists. |
| **10** | `sys-encoding` | `sys.stdout.reconfigure()` | Handled cross-platform terminal UTF-8 character encoding on Windows (`cp1252` workaround) using `sys.stdout.reconfigure(encoding="utf-8")`. |

---

## ⚡ Zero-Dependency Proof

- **Runtime `requirements.txt`**: Empty / Not required.
- **Build / Execution Command**:
  ```bash
  python Logic/code.py
  ```
- **Dependencies**: `0` third-party runtime packages.
