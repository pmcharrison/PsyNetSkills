"""Upload configuration for direct browser video uploads.

Production deployments can set `VIDEO_RECORDING_S3_BUCKET` to return a
presigned PUT URL. Local tests default to a filesystem-backed S3-like endpoint
so the browser still uploads directly without using PsyNet media storage.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from psynet.api import expose_to_api

CONTENT_TYPE = "video/webm"
LOCAL_BUCKET = "local-video-recording-test-bucket"
LOCAL_ROOT = Path("local_s3_recordings")


def recording_s3_key(recording_id: str) -> str:
    return f"recordings/{recording_id}.webm"


def build_upload_config(recording_id: str) -> dict:
    bucket = os.environ.get("VIDEO_RECORDING_S3_BUCKET")
    s3_key = recording_s3_key(recording_id)

    if bucket:
        return _build_presigned_s3_config(bucket=bucket, s3_key=s3_key, recording_id=recording_id)

    return {
        "mode": "local_test_s3",
        "bucket": LOCAL_BUCKET,
        "s3_key": s3_key,
        "s3_url": f"s3://{LOCAL_BUCKET}/{s3_key}",
        "upload_url": "/api/video_recording_upload",
        "content_type": CONTENT_TYPE,
        "simulate": os.environ.get("VIDEO_RECORDING_SIMULATE_CAMERA", "0") == "1",
    }


def _build_presigned_s3_config(bucket: str, s3_key: str, recording_id: str) -> dict:
    from psynet.media import get_s3_client, setup_bucket_for_presigned_urls

    client = get_s3_client()
    setup_bucket_for_presigned_urls(bucket_name=bucket)
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": s3_key,
            "ContentType": CONTENT_TYPE,
        },
        ExpiresIn=3600,
    )
    return {
        "mode": "s3_presigned_put",
        "bucket": bucket,
        "s3_key": s3_key,
        "s3_url": f"s3://{bucket}/{s3_key}",
        "upload_url": upload_url,
        "content_type": CONTENT_TYPE,
        "simulate": os.environ.get("VIDEO_RECORDING_SIMULATE_CAMERA", "0") == "1",
    }


@expose_to_api("video_recording_upload_config")
def video_recording_upload_config(recording_id: str):
    return build_upload_config(recording_id)


@expose_to_api("video_recording_upload")
def video_recording_upload(
    recording_id: str,
    s3_key: str,
    content_type: str,
    data_base64: str,
):
    if not s3_key.startswith("recordings/") or ".." in s3_key:
        raise ValueError("Invalid local S3 key.")

    destination = LOCAL_ROOT / s3_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = base64.b64decode(data_base64)
    destination.write_bytes(payload)

    manifest_path = LOCAL_ROOT / "manifest.jsonl"
    with manifest_path.open("a", encoding="utf-8") as manifest:
        manifest.write(
            json.dumps(
                {
                    "recording_id": recording_id,
                    "bucket": LOCAL_BUCKET,
                    "s3_key": s3_key,
                    "s3_url": f"s3://{LOCAL_BUCKET}/{s3_key}",
                    "content_type": content_type,
                    "bytes": len(payload),
                },
                sort_keys=True,
            )
            + "\n"
        )

    return {
        "ok": True,
        "recording_id": recording_id,
        "s3_key": s3_key,
        "s3_url": f"s3://{LOCAL_BUCKET}/{s3_key}",
        "bytes": len(payload),
    }
