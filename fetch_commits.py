import requests
import csv

def fetch_and_save_commits():
    owner = "facebook"
    repo = "react"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"

    print(f"Fetching data from {api_url}...")
    response = requests.get(api_url)

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
                writer.writerow([repo, commit_date, commit_message])
                
        print("Success! Open 'commit_history.csv' to see your data.")
    else:
        print(f"Error: Could not connect to API. Status code {response.status_code}")

if __name__ == "__main__":
    fetch_and_save_commits()
