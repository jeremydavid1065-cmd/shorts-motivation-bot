from __future__ import annotations

from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

REPO_ROOT = Path(__file__).resolve().parents[2]
SECRETS_DIR = REPO_ROOT / "secrets"
TOKEN_FILE = SECRETS_DIR / "token.json"

TEST_VIDEO = REPO_ROOT / "tmp" / "upload_test.mp4"


def main() -> None:
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(f"Missing token file: {TOKEN_FILE}. Run youtube_auth first.")
    if not TEST_VIDEO.exists():
        raise FileNotFoundError(f"Missing test video: {TEST_VIDEO}")

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    youtube = build("youtube", "v3", credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Shorts Motivation Bot - Upload Test",
                "description": "Automated upload test from laptop worker.",
                "tags": ["test", "automation"],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "unlisted",
                "selfDeclaredMadeForKids": False,
            },
        },
        media_body=MediaFileUpload(str(TEST_VIDEO), mimetype="video/mp4", resumable=True),
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print("Upload complete!")
    print("Video ID:", response.get("id"))
    print("URL: https://www.youtube.com/watch?v=" + response.get("id"))


if __name__ == "__main__":
    main()