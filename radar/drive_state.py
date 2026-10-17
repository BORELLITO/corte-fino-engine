from __future__ import annotations

import io
import os
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

from radar.upload_reports_drive import (
    FOLDER_MIME,
    RADAR_FOLDER_NAME,
    credentials_from_env,
    find_or_create_folder,
    normalize_folder_id,
)

STATE_NAME = "history.json"
STATE_PATH = Path(__file__).resolve().parent / "state" / STATE_NAME


def get_drive():
    return build(
        "drive",
        "v3",
        credentials=credentials_from_env(),
        cache_discovery=False,
    )


def get_radar_folder(drive) -> str:
    base_folder = normalize_folder_id(os.environ.get("DRIVE_FOLDER_ID", ""))
    if not base_folder:
        raise SystemExit("DRIVE_FOLDER_ID ausente.")
    parent = drive.files().get(
        fileId=base_folder,
        fields="id,mimeType,trashed,capabilities(canAddChildren)",
    ).execute(num_retries=3)
    if parent.get("mimeType") != FOLDER_MIME or parent.get("trashed"):
        raise SystemExit("DRIVE_FOLDER_ID não aponta para uma pasta ativa.")
    if parent.get("capabilities", {}).get("canAddChildren") is False:
        raise SystemExit("Sem permissão de escrita em DRIVE_FOLDER_ID.")
    return find_or_create_folder(drive, base_folder, RADAR_FOLDER_NAME)


def find_state(drive, folder_id: str) -> dict | None:
    query = (
        f"'{folder_id}' in parents and trashed = false and "
        f"name = '{STATE_NAME}'"
    )
    files = drive.files().list(
        q=query,
        pageSize=10,
        fields="files(id,name,size,modifiedTime)",
    ).execute(num_retries=3).get("files", [])
    if len(files) > 1:
        raise RuntimeError("Duplicidade de history.json detectada no Drive.")
    return files[0] if files else None


def pull() -> int:
    drive = get_drive()
    folder_id = get_radar_folder(drive)
    state = find_state(drive, folder_id)
    if not state:
        print("Nenhum histórico remoto; primeira rodada da V2.1.")
        return 0

    request = drive.files().get_media(fileId=state["id"])
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk(num_retries=3)

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_bytes(buffer.getvalue())
    print("Histórico de momentum restaurado do Google Drive.")
    return 0


def push() -> int:
    if not STATE_PATH.is_file():
        raise SystemExit("history.json não foi gerado.")

    drive = get_drive()
    folder_id = get_radar_folder(drive)
    state = find_state(drive, folder_id)
    media = MediaFileUpload(
        str(STATE_PATH),
        mimetype="application/json",
        resumable=False,
    )
    if state:
        drive.files().update(
            fileId=state["id"],
            media_body=media,
            fields="id,name,size,modifiedTime",
        ).execute(num_retries=3)
    else:
        drive.files().create(
            body={"name": STATE_NAME, "parents": [folder_id]},
            media_body=media,
            fields="id,name,size,modifiedTime",
        ).execute(num_retries=3)

    print("Histórico de momentum salvo no Google Drive.")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("pull", "push"))
    args = parser.parse_args()
    return pull() if args.action == "pull" else push()


if __name__ == "__main__":
    raise SystemExit(main())
