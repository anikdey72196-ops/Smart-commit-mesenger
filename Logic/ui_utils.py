import sys
import time
import threading
import os

# Reconfigure stdout/stderr for UTF-8 encoding on Windows to handle unicode emojis
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Try importing rich for enhanced UI, fallback to ANSI colors
HAS_RICH = False
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt
    from rich.text import Text
    from rich.style import Style
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None

# ANSI Color Codes for Fallback
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"

class Spinner:
    """Animated terminal spinner for long-running operations."""
    def __init__(self, message="Thinking..."):
        self.message = message
        self.stop_running = False
        self.thread = None
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __enter__(self):
        if HAS_RICH:
            self._rich_progress = Progress(
                SpinnerColumn(spinner_name="dots"),
                TextColumn(f"[cyan]{self.message}[/cyan]"),
                transient=True
            )
            self._rich_progress.start()
            self._rich_task = self._rich_progress.add_task("spin")
        else:
            self.stop_running = False
            self.thread = threading.Thread(target=self._spin, daemon=True)
            self.thread.start()
        return self

    def _spin(self):
        idx = 0
        while not self.stop_running:
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f"\r{CYAN}{frame}{RESET} {BOLD}{self.message}{RESET}")
            sys.stdout.flush()
            time.sleep(0.08)
            idx += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        if HAS_RICH:
            self._rich_progress.stop()
        else:
            self.stop_running = True
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=0.2)
            sys.stdout.write("\r\033[K") # Clear line
            sys.stdout.flush()

def print_banner():
    """Prints a stylish ASCII header banner."""
    if HAS_RICH:
        title = Text("🚀 SMART COMMIT MESSENGER", style="bold cyan")
        subtitle = Text("Local AI-Powered Git Workflow Automation", style="dim white")
        console.print(Panel.fit(f"{title}\n{subtitle}", border_style="bold blue"))
    else:
        print(f"\n{CYAN}{BOLD}===================================================={RESET}")
        print(f"{CYAN}{BOLD} 🚀 SMART COMMIT MESSENGER{RESET}")
        print(f"{DIM} Local AI-Powered Git Workflow Automation{RESET}")
        print(f"{CYAN}{BOLD}===================================================={RESET}\n")

def print_diff_stats(stats_text, branch_name=""):
    """Displays formatted git diff statistics."""
    if not stats_text:
        return
    
    if HAS_RICH:
        header = f"[bold yellow]Branch:[/bold yellow] [green]{branch_name}[/green]\n" if branch_name else ""
        formatted_stats = stats_text.replace("+", "[green]+[/green]").replace("-", "[red]-[/red]")
        console.print(Panel(f"{header}{formatted_stats}", title="📊 Detected Changes", border_style="yellow"))
    else:
        branch_info = f"{YELLOW}Branch:{RESET} {GREEN}{branch_name}{RESET}\n" if branch_name else ""
        print(f"{BOLD}📊 Detected Changes:{RESET}")
        if branch_info:
            print(f"   {branch_info}")
        for line in stats_text.splitlines():
            # Colorize insertions and deletions
            colored_line = line.replace("+", f"{GREEN}+{RESET}").replace("-", f"{RED}-{RESET}")
            print(f"   {colored_line}")
        print()

def print_options(options):
    """Prints the 3 generated commit message options in a formatted panel."""
    if HAS_RICH:
        content = ""
        for idx, opt in enumerate(options, 1):
            content += f"[bold cyan][{idx}][/bold cyan] {opt}\n"
        content += "\n[bold yellow][e][/bold yellow] Edit / Custom Message\n"
        content += "[bold red][c][/bold red] Cancel Commit"
        console.print(Panel(content, title="✨ AI Suggested Commit Messages", border_style="magenta"))
    else:
        print(f"{MAGENTA}{BOLD}✨ AI Suggested Commit Messages:{RESET}")
        for idx, opt in enumerate(options, 1):
            print(f"  {CYAN}{BOLD}[{idx}]{RESET} {opt}")
        print(f"  {YELLOW}{BOLD}[e]{RESET} Edit / Enter custom message")
        print(f"  {RED}{BOLD}[c]{RESET} Cancel commit")
        print()

def print_success(message):
    """Prints a success message."""
    if HAS_RICH:
        console.print(f"[bold green]✔ {message}[/bold green]")
    else:
        print(f"{GREEN}{BOLD}✔ {message}{RESET}")

def print_warning(message):
    """Prints a warning message."""
    if HAS_RICH:
        console.print(f"[bold yellow]⚠️ {message}[/bold yellow]")
    else:
        print(f"{YELLOW}{BOLD}⚠️ {message}{RESET}")

def print_error(message):
    """Prints an error message."""
    if HAS_RICH:
        console.print(f"[bold red]❌ {message}[/bold red]")
    else:
        print(f"{RED}{BOLD}❌ {message}{RESET}")
