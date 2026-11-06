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
        subtitle = Text("Local AI-Powered Git Workflow & Merging Agent", style="dim white")
        console.print(Panel.fit(f"{title}\n{subtitle}", border_style="bold blue"))
    else:
        print(f"\n{CYAN}{BOLD}===================================================={RESET}")
        print(f"{CYAN}{BOLD} 🚀 SMART COMMIT MESSENGER{RESET}")
        print(f"{DIM} Local AI-Powered Git Workflow & Merging Agent{RESET}")
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

def print_incoming_commits(commits, branch_name=""):
    """Displays incoming commits from teammates on remote."""
    if not commits:
        return

    count = len(commits)
    title = f"🔔 Teammate Updates Detected ({count} new commit{'s' if count > 1 else ''})"

    if HAS_RICH:
        content = ""
        for c in commits:
            h = f"[bold cyan]{c.get('hash', '')}[/bold cyan]"
            a = f"[bold yellow]{c.get('author', 'Unknown')}[/bold yellow]"
            t = f"[dim]({c.get('time', '')})[/dim]"
            m = c.get('message', '')
            content += f"• {h} by {a} {t}: {m}\n"
        console.print(Panel(content.strip(), title=title, border_style="cyan"))
    else:
        print(f"\n{CYAN}{BOLD}🔔 Teammate Updates Detected ({count} new commit{'s' if count > 1 else ''}):{RESET}")
        for c in commits:
            h = f"{CYAN}{BOLD}{c.get('hash', '')}{RESET}"
            a = f"{YELLOW}{c.get('author', 'Unknown')}{RESET}"
            t = f"{DIM}({c.get('time', '')}){RESET}"
            m = c.get('message', '')
            print(f"  • {h} by {a} {t}: {m}")
        print()

def print_branch_status(current_branch, upstream=None):
    """Prints active branch status."""
    if HAS_RICH:
        up_text = f" [dim](tracks [cyan]{upstream}[/cyan])[/dim]" if upstream else ""
        console.print(f"[bold yellow]🌿 Active Branch:[/bold yellow] [bold green]{current_branch}[/bold green]{up_text}")
    else:
        up_text = f" (tracks {upstream})" if upstream else ""
        print(f"{YELLOW}{BOLD}🌿 Active Branch:{RESET} {GREEN}{BOLD}{current_branch}{RESET}{DIM}{up_text}{RESET}")

def print_branch_list(branches, current_branch=None):
    """Displays formatted list of branches for switching or merging."""
    if not branches:
        print_warning("No branches found.")
        return

    if HAS_RICH:
        content = ""
        for idx, b in enumerate(branches, 1):
            is_cur = " [bold green](current)[/bold green]" if b == current_branch else ""
            content += f"[bold cyan][{idx}][/bold cyan] {b}{is_cur}\n"
        console.print(Panel(content.strip(), title="🌿 Available Branches", border_style="blue"))
    else:
        print(f"\n{CYAN}{BOLD}🌿 Available Branches:{RESET}")
        for idx, b in enumerate(branches, 1):
            is_cur = f" {GREEN}(current){RESET}" if b == current_branch else ""
            print(f"  {CYAN}{BOLD}[{idx}]{RESET} {b}{is_cur}")
        print()

def print_conflict_report(conflicts):
    """Displays a warning panel for merge conflicts."""
    if not conflicts:
        return

    if HAS_RICH:
        content = "[bold red]Automatic merge failed due to conflicting changes in:[/bold red]\n"
        for f in conflicts:
            content += f"  • [bold yellow]{f}[/bold yellow]\n"
        console.print(Panel(content.strip(), title="⚠️ MERGE CONFLICT DETECTED", border_style="red"))
    else:
        print(f"\n{RED}{BOLD}⚠️ MERGE CONFLICT DETECTED:{RESET}")
        print(f"{RED}Automatic merge failed due to conflicting changes in:{RESET}")
        for f in conflicts:
            print(f"  • {YELLOW}{BOLD}{f}{RESET}")
        print()

def print_conflict_options():
    """Displays resolution choices when conflicts occur."""
    if HAS_RICH:
        content = (
            "[bold cyan][1][/bold cyan] Keep conflict markers (resolve manually in code editor)\n"
            "[bold magenta][2][/bold magenta] Explain conflicts with AI (get step-by-step resolution advice)\n"
            "[bold red][3][/bold red] Abort merge (restore working directory)"
        )
        console.print(Panel(content, title="🛠️ Merge Resolution Options", border_style="yellow"))
    else:
        print(f"{YELLOW}{BOLD}🛠️ Merge Resolution Options:{RESET}")
        print(f"  {CYAN}{BOLD}[1]{RESET} Keep conflict markers (resolve manually in code editor)")
        print(f"  {MAGENTA}{BOLD}[2]{RESET} Explain conflicts with AI (get step-by-step resolution advice)")
        print(f"  {RED}{BOLD}[3]{RESET} Abort merge (restore working directory)")
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
