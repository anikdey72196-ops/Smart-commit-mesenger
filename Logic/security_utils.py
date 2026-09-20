import re
import os
import sys

# High-risk sensitive files that should almost never be committed
SENSITIVE_FILE_PATTERNS = [
    r"(^|/)\.env(\.[a-zA-Z0-9_-]+)?$",  # .env, .env.local, .env.production (excluding .env.example)
    r"(^|/)id_(rsa|ed25519|dsa|ecdsa)(\.pub)?$",
    r"\.(pem|key|pkcs12|pfx|p12|kdbx)$",
    r"(^|/)(credentials|client_secret|service[-_]account)[-_a-zA-Z0-9]*\.json$",
]

# Patterns for hardcoded credentials and API keys
SECRET_PATTERNS = [
    ("Private Key", re.compile(r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----")),
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub Token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b")),
    ("Google / Gemini API Key", re.compile(r"\bAIza[0-9A-Za-z\-_]{34,36}\b")),
    ("OpenAI API Key", re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b")),
    ("Slack Token", re.compile(r"\bxox[baprs]-[0-9a-zA-Z]{10,}\b")),
    ("Generic Secret / API Key", re.compile(
        r"""(?i)(?:api[_-]?key|access[_-]?token|secret[_-]?key|client[_-]?secret|auth[_-]?token)\s*[:=]\s*['"][A-Za-z0-9_\-\.]{14,}['"]"""
    )),
]

# Patterns for stray debuggers / logging
DEBUG_PATTERNS = [
    ("Python Breakpoint / PDB", re.compile(r"\b(?:breakpoint\(\)|pdb\.set_trace\(\)|import\s+pdb)\b")),
    ("JavaScript Debugger", re.compile(r"\bdebugger;?\b")),
    ("JavaScript Console Log", re.compile(r"\bconsole\.(?:log|debug|trace)\(")),
]

def mask_secret(text):
    """Masks secret characters for safe console display."""
    if len(text) <= 8:
        return "****"
    return text[:4] + "*" * (len(text) - 8) + text[-4:]

def scan_diff_for_secrets(diff_text):
    """Scans git diff text for accidentally staged sensitive files, secrets, and debuggers."""
    findings = []
    
    current_file = "Unknown"
    
    for line in diff_text.splitlines():
        # Track file being modified
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 4:
                # b/filepath
                current_file = parts[3].lstrip("b/")
                
                # Check for sensitive files (skip .env.example)
                if not current_file.endswith(".example") and not current_file.endswith(".sample"):
                    for file_pattern in SENSITIVE_FILE_PATTERNS:
                        if re.search(file_pattern, current_file, re.IGNORECASE):
                            findings.append({
                                "type": "SENSITIVE_FILE",
                                "severity": "CRITICAL",
                                "file": current_file,
                                "description": f"Potentially sensitive file '{current_file}' detected in commit",
                                "snippet": current_file
                            })
                            break

        # Only scan added lines in the diff
        if line.startswith("+") and not line.startswith("+++"):
            added_content = line[1:].strip()
            
            # 1. Check for Secrets (CRITICAL)
            for label, pattern in SECRET_PATTERNS:
                match = pattern.search(added_content)
                if match:
                    matched_str = match.group(0)
                    findings.append({
                        "type": "SECRET",
                        "severity": "CRITICAL",
                        "file": current_file,
                        "description": f"Potential {label} detected in {current_file}",
                        "snippet": mask_secret(matched_str)
                    })
            
            # 2. Check for Debug Statements (WARNING)
            for label, pattern in DEBUG_PATTERNS:
                match = pattern.search(added_content)
                if match:
                    findings.append({
                        "type": "DEBUG",
                        "severity": "WARNING",
                        "file": current_file,
                        "description": f"Stray {label} detected in {current_file}",
                        "snippet": match.group(0)
                    })

    has_critical = any(f["severity"] == "CRITICAL" for f in findings)
    has_warnings = any(f["severity"] == "WARNING" for f in findings)
    
    return {
        "has_critical": has_critical,
        "has_warnings": has_warnings,
        "findings": findings
    }

def print_security_report(report):
    """Displays a clean visual security report in terminal."""
    if not report["findings"]:
        return

    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{RED}{BOLD}🛡️  PRE-COMMIT SECURITY GUARDRAILS ALERT{RESET}")
    print(f"{RED}----------------------------------------------------{RESET}")

    for item in report["findings"]:
        sev = item["severity"]
        color = RED if sev == "CRITICAL" else YELLOW
        print(f" {color}[{sev}]{RESET} {BOLD}{item['description']}{RESET}")
        print(f"   {CYAN}File:{RESET} {item['file']} | {CYAN}Match:{RESET} {item['snippet']}")

    print(f"{RED}----------------------------------------------------{RESET}")
