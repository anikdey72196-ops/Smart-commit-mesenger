import requests
import csv

def sanitize_csv_field(field):
    field_str = str(field)
    if field_str.startswith(('=', '+', '-', '@')):
        return "'" + field_str
    return field_str

def fetch_and_save_commits():
    owner = "facebook"
    repo = "react"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"

    print(f"Fetching data from {api_url}...")
    response = requests.get(api_url, timeout=10)

    if response.status_code == 200:
        commits_data = response.json()
        
        with open("commit_history.csv", "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Repository", "Date", "Message"])
            
            for commit_item in commits_data:
                # Extract the required fields
                commit_date = commit_item["commit"]["author"]["date"]
                commit_message = commit_item["commit"]["message"]
                
                # Write to the CSV
                writer.writerow([sanitize_csv_field(repo), sanitize_csv_field(commit_date), sanitize_csv_field(commit_message)])
                
        print("Success! Open 'commit_history.csv' to see your data.")
    else:
        print(f"Error: Could not connect to API. Status code {response.status_code}")

if __name__ == "__main__":
    fetch_and_save_commits()
