"""Utility functions for uploading images to Alibaba Cloud OSS."""

import base64
import logging
import mimetypes
import uuid
from datetime import datetime

import httpx
import oss2

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_oss_bucket() -> oss2.Bucket:
    """Create and return an OSS Bucket instance using application settings."""
    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)


# Keep backward-compatible alias
_get_bucket = _get_oss_bucket


def _generate_object_key(extension: str = "png") -> str:
    """Generate a unique object key for OSS storage.

    Format: ai-generated/{YYYYMMDD}/{uuid}.{ext}

    Args:
        extension: File extension without dot. Defaults to "png".

    Returns:
        A unique object key like "ai-generated/20250101/uuid.png".
    """
    date_path = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex
    return f"ai-generated/{date_path}/{unique_id}.{extension}"


def generate_oss_filename(prefix: str, extension: str = "png") -> str:
    """Generate a unique filename for OSS storage.

    Args:
        prefix: Path prefix (e.g., "ai-images/wishes").
        extension: File extension without dot. Defaults to "png".

    Returns:
        A unique object key like "ai-images/wishes/20250101/uuid.png".
    """
    date_path = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex
    return f"{prefix}/{date_path}/{unique_id}.{extension}"


def _extension_from_content_type(content_type: str) -> str:
    """Extract file extension from a content type string.

    Args:
        content_type: MIME type like "image/png" or "image/jpeg".

    Returns:
        Extension string without dot (e.g., "png", "jpeg").
    """
    ext = mimetypes.guess_extension(content_type)
    if ext:
        return ext.lstrip(".")
    # Fallback: try to extract from content_type directly
    if "/" in content_type:
        return content_type.split("/")[-1]
    return "png"


def upload_image_to_oss(image_data: bytes, filename: str) -> str:
    """Upload image bytes to Alibaba Cloud OSS.

    Args:
        image_data: Raw image bytes to upload.
        filename: The object key (path) in the OSS bucket.

    Returns:
        The public URL of the uploaded image.

    Raises:
        oss2.exceptions.OssError: If the upload fails.
    """
    bucket = _get_oss_bucket()
    bucket.put_object(filename, image_data)
    base_url = settings.OSS_BASE_URL.rstrip("/")
    return f"{base_url}/{filename}"


def upload_image_from_url(image_url: str, object_key: str | None = None) -> str:
    """Download an image from a URL and upload it to OSS.

    Args:
        image_url: The URL to download the image from.
        object_key: The object key (path) in the OSS bucket.
            If None, auto-generates using UUID + timestamp.

    Returns:
        The public URL of the uploaded image.

    Raises:
        httpx.HTTPStatusError: If the download fails.
        oss2.exceptions.OssError: If the upload fails.
    """
    try:
        response = httpx.get(image_url, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error("Failed to download image from %s: %s", image_url, e)
        raise

    if object_key is None:
        # Try to determine extension from content-type header
        content_type = response.headers.get("content-type", "image/png")
        ext = _extension_from_content_type(content_type)
        object_key = _generate_object_key(ext)

    try:
        return upload_image_to_oss(response.content, object_key)
    except Exception as e:
        logger.error("Failed to upload image to OSS (key=%s): %s", object_key, e)
        raise


def upload_image_from_bytes(
    data: bytes, content_type: str, object_key: str | None = None
) -> str:
    """Upload raw image bytes to OSS.

    Args:
        data: Raw image bytes to upload.
        content_type: MIME type of the image (e.g., "image/png").
        object_key: The object key (path) in the OSS bucket.
            If None, auto-generates using UUID + timestamp.

    Returns:
        The public URL of the uploaded image.

    Raises:
        oss2.exceptions.OssError: If the upload fails.
    """
    if object_key is None:
        ext = _extension_from_content_type(content_type)
        object_key = _generate_object_key(ext)

    try:
        return upload_image_to_oss(data, object_key)
    except Exception as e:
        logger.error("Failed to upload image bytes to OSS (key=%s): %s", object_key, e)
        raise


def upload_image_from_base64(
    base64_data: str, object_key: str | None = None
) -> str:
    """Decode base64 image data and upload to OSS.

    Handles the "data:image/png;base64,..." prefix format as well as
    raw base64 strings.

    Args:
        base64_data: Base64-encoded image data, optionally with data URI prefix.
        object_key: The object key (path) in the OSS bucket.
            If None, auto-generates using UUID + timestamp.

    Returns:
        The public URL of the uploaded image.

    Raises:
        ValueError: If the base64 data is invalid.
        oss2.exceptions.OssError: If the upload fails.
    """
    content_type = "image/png"  # default

    # Strip data URI prefix if present (e.g., "data:image/png;base64,...")
    if base64_data.startswith("data:"):
        try:
            header, base64_data = base64_data.split(",", 1)
            # Extract content type from header like "data:image/jpeg;base64"
            mime_part = header.split(";")[0]  # "data:image/jpeg"
            content_type = mime_part.replace("data:", "")
        except (ValueError, IndexError):
            logger.warning("Could not parse data URI prefix, using default content type")

    try:
        image_bytes = base64.b64decode(base64_data)
    except Exception as e:
        logger.error("Failed to decode base64 image data: %s", e)
        raise ValueError(f"Invalid base64 data: {e}") from e

    if object_key is None:
        ext = _extension_from_content_type(content_type)
        object_key = _generate_object_key(ext)

    try:
        return upload_image_to_oss(image_bytes, object_key)
    except Exception as e:
        logger.error(
            "Failed to upload base64 image to OSS (key=%s): %s", object_key, e
        )
        raise
