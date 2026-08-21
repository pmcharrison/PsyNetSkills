"""Real S3 upload configuration for browser-direct video recording."""

from __future__ import annotations

import os

from psynet.media import get_s3_client, setup_bucket_for_presigned_urls

CONTENT_TYPE = "video/webm"


class MissingS3Configuration(RuntimeError):
    """Raised when the experiment cannot safely configure real S3 uploads."""


def recording_s3_key(recording_id: str) -> str:
    return f"recordings/{recording_id}.webm"


def build_upload_config(recording_id: str) -> dict:
    """Return a short-lived browser PUT URL for a recording.

    This helper deliberately has no local-storage fallback: the challenge is
    specifically about real S3 streaming. If a safe bucket is not configured,
    the attempt should record a blocker rather than pretending a local stub
    satisfies the requirement.
    """

    bucket = os.environ.get("VIDEO_RECORDING_S3_BUCKET")
    if not bucket:
        raise MissingS3Configuration(
            "VIDEO_RECORDING_S3_BUCKET is not set; real S3 upload evidence cannot be collected."
        )

    s3_key = recording_s3_key(recording_id)
    setup_bucket_for_presigned_urls(bucket_name=bucket)
    upload_url = get_s3_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": s3_key,
            "ContentType": CONTENT_TYPE,
        },
        ExpiresIn=3600,
    )
    return {
        "bucket": bucket,
        "s3_key": s3_key,
        "s3_url": f"s3://{bucket}/{s3_key}",
        "upload_url": upload_url,
        "content_type": CONTENT_TYPE,
    }
