from pathlib import Path
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def main():
    flow = InstalledAppFlow.from_client_secrets_file("private/credentials.json", ["https://www.googleapis.com/auth/gmail.readonly"])
    creds = flow.run_local_server(port=0)
    service = build("gmail", "v1", credentials=creds)
    ids = service.users().messages().list(userId="me", maxResults=10, q="in:inbox").execute().get("messages", [])
    for item in ids:
        msg = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        print(json.dumps({"id":item["id"],"subject":headers.get("subject",""),"body":msg.get("snippet",""),"partial":True}, ensure_ascii=False))
if __name__ == "__main__":
    main()
