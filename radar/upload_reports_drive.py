from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

REPORT_NAMES = (
    "radar_latest.md",
    "radar_latest.json",
    "radar_latest.csv",
)
FOLDER_MIME = "application/vnd.google-apps.folder"
RADAR_FOLDER_NAME = "RADAR_CORTE_FINO"


def normalize_folder_id(value: str) -> str:
    value = (value or "").strip()
    if "/folders/" in value:
        value = value.split("/folders/", 1)[1].split("?", 1)[0].split("/", 1)[0].strip()
    return value


def credentials_from_env() -> Credentials:
    required = (
        "GOOGLE_REFRESH_TOKEN",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
    )
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise SystemExit("Secrets ausentes: " + ", ".join(missing))

    credentials = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    credentials.refresh(Request())
    return credentials


def find_or_create_folder(drive, parent_id: str, name: str) -> str:
    escaped = name.replace("'", "\\'")
    query = (
        f"'{parent_id}' in parents and trashed = false and "
        f"mimeType = '{FOLDER_MIME}' and name = '{escaped}'"
    )
    files = drive.files().list(
        q=query,
        pageSize=10,
        fields="files(id,name,mimeType)",
    ).execute(num_retries=3).get("files", [])
    if files:
        return files[0]["id"]

    created = drive.files().create(
        body={
            "name": name,
            "mimeType": FOLDER_MIME,
            "parents": [parent_id],
        },
        fields="id",
    ).execute(num_retries=3)
    return created["id"]


def upsert_file(drive, folder_id: str, path: Path) -> None:
    escaped = path.name.replace("'", "\\'")
    query = (
        f"'{folder_id}' in parents and trashed = false and "
        f"name = '{escaped}'"
    )
    files = drive.files().list(
        q=query,
        pageSize=10,
        fields="files(id,name)",
    ).execute(num_retries=3).get("files", [])

    media = MediaFileUpload(
        str(path),
        mimetype="text/markdown" if path.suffix == ".md"
        else "application/json" if path.suffix == ".json"
        else "text/csv",
        resumable=False,
    )
    if files:
        drive.files().update(
            fileId=files[0]["id"],
            media_body=media,
            fields="id,name",
        ).execute(num_retries=3)
    else:
        drive.files().create(
            body={"name": path.name, "parents": [folder_id]},
            media_body=media,
            fields="id,name",
        ).execute(num_retries=3)


def main() -> int:
    base_folder = normalize_folder_id(os.environ.get("DRIVE_FOLDER_ID", ""))
    if not base_folder:
        raise SystemExit("DRIVE_FOLDER_ID ausente.")

    output_dir = Path(__file__).resolve().parent / "output"
    missing = [name for name in REPORT_NAMES if not (output_dir / name).is_file()]
    if missing:
        raise SystemExit("Relatórios ausentes: " + ", ".join(missing))

    drive = build(
        "drive",
        "v3",
        credentials=credentials_from_env(),
        cache_discovery=False,
    )
    radar_folder = find_or_create_folder(drive, base_folder, RADAR_FOLDER_NAME)
    for name in REPORT_NAMES:
        upsert_file(drive, radar_folder, output_dir / name)

    print("Radar enviado ao Google Drive privado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
