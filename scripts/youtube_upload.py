#!/usr/bin/env python3
from __future__ import annotations
import os
import sys
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload(path, title, description, tags, privacy="public"):
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(
            path, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True
        ),
    )
    response = None
    for attempt in range(8):
        try:
            while response is None:
                _, response = request.next_chunk()
            video_id = response["id"]
            print("YouTube video:", video_id)
            print("https://www.youtube.com/watch?v=" + video_id)
            return video_id
        except HttpError as exc:
            if exc.resp.status not in (500, 502, 503, 504):
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("YouTube upload failed after retries")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit("usage: youtube_upload.py VIDEO TITLE DESCRIPTION [tags...]")
    upload(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4:],
        os.getenv("YOUTUBE_PRIVACY", "public"),
    )
