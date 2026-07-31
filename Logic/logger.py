import os
import csv
import datetime

def log_commit(commit_msg):
    try:
        repo_name = os.path.basename(os.path.abspath(os.getcwd()))
        owner_name = "anikdey72196"
        commit_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Save the CSV in the parent directory (the master folder)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(os.path.dirname(script_dir), "commit_history.csv")
        file_exists = os.path.isfile(csv_path)
        
        with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if not file_exists:
                writer.writerow(["Owner", "Repository", "Date", "Message"])
            writer.writerow([owner_name, repo_name, commit_date, commit_msg])
    except Exception as e:
        print(f"Failed to save to CSV log: {e}")
