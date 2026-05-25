"""Tests for OSS utility functions."""

import base64
from unittest.mock import MagicMock, patch

import pytest

from app.utils.oss import (
    _extension_from_content_type,
    _generate_object_key,
    generate_oss_filename,
    upload_image_from_base64,
    upload_image_from_bytes,
    upload_image_from_url,
    upload_image_to_oss,
)


class TestGenerateObjectKey:
    """Tests for _generate_object_key."""

    def test_generates_unique_keys(self):
        """Each call should produce a different key."""
        key1 = _generate_object_key("png")
        key2 = _generate_object_key("png")
        assert key1 != key2

    def test_starts_with_ai_generated_prefix(self):
        """The key should start with 'ai-generated/'."""
        key = _generate_object_key("png")
        assert key.startswith("ai-generated/")

    def test_default_extension_is_png(self):
        """Default extension should be png."""
        key = _generate_object_key()
        assert key.endswith(".png")

    def test_custom_extension(self):
        """Should support custom file extensions."""
        key = _generate_object_key("jpg")
        assert key.endswith(".jpg")

    def test_includes_date_path(self):
        """The key should include a date-based path segment."""
        key = _generate_object_key("png")
        parts = key.split("/")
        # ai-generated/YYYYMMDD/uuid.ext
        assert len(parts) == 3
        assert parts[0] == "ai-generated"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert parts[1].isdigit()


class TestGenerateOssFilename:
    """Tests for generate_oss_filename."""

    def test_generates_unique_filenames(self):
        """Each call should produce a different filename."""
        name1 = generate_oss_filename("images")
        name2 = generate_oss_filename("images")
        assert name1 != name2

    def test_includes_prefix(self):
        """The filename should start with the given prefix."""
        name = generate_oss_filename("ai-images/wishes")
        assert name.startswith("ai-images/wishes/")

    def test_default_extension_is_png(self):
        """Default extension should be png."""
        name = generate_oss_filename("images")
        assert name.endswith(".png")

    def test_custom_extension(self):
        """Should support custom file extensions."""
        name = generate_oss_filename("images", extension="jpg")
        assert name.endswith(".jpg")

    def test_includes_date_path(self):
        """The filename should include a date-based path segment."""
        name = generate_oss_filename("prefix")
        parts = name.split("/")
        # prefix/YYYYMMDD/uuid.ext
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert parts[1].isdigit()


class TestExtensionFromContentType:
    """Tests for _extension_from_content_type."""

    def test_png(self):
        assert _extension_from_content_type("image/png") == "png"

    def test_jpeg(self):
        result = _extension_from_content_type("image/jpeg")
        assert result in ("jpeg", "jpg", "jpe")

    def test_webp(self):
        assert _extension_from_content_type("image/webp") == "webp"

    def test_unknown_type_uses_suffix(self):
        """For unknown types, should extract from the type string."""
        result = _extension_from_content_type("image/custom-format")
        assert result == "custom-format"


class TestUploadImageToOss:
    """Tests for upload_image_to_oss."""

    @patch("app.utils.oss._get_oss_bucket")
    @patch("app.utils.oss.settings")
    def test_uploads_and_returns_url(self, mock_settings, mock_get_bucket):
        """Should upload data and return the public URL."""
        mock_settings.OSS_BASE_URL = "https://cdn.example.com"
        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket

        image_data = b"\x89PNG\r\n\x1a\n fake image data"
        filename = "ai-generated/20250101/abc123.png"

        result = upload_image_to_oss(image_data, filename)

        mock_bucket.put_object.assert_called_once_with(filename, image_data)
        assert result == "https://cdn.example.com/ai-generated/20250101/abc123.png"

    @patch("app.utils.oss._get_oss_bucket")
    @patch("app.utils.oss.settings")
    def test_strips_trailing_slash_from_base_url(self, mock_settings, mock_get_bucket):
        """Should handle trailing slash in OSS_BASE_URL."""
        mock_settings.OSS_BASE_URL = "https://cdn.example.com/"
        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket

        result = upload_image_to_oss(b"data", "path/file.png")

        assert result == "https://cdn.example.com/path/file.png"


class TestUploadImageFromUrl:
    """Tests for upload_image_from_url."""

    @patch("app.utils.oss.upload_image_to_oss")
    @patch("app.utils.oss.httpx.get")
    def test_downloads_and_uploads_with_explicit_key(self, mock_httpx_get, mock_upload):
        """Should download from URL then upload to OSS with given key."""
        mock_response = MagicMock()
        mock_response.content = b"downloaded image bytes"
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-type": "image/png"}
        mock_httpx_get.return_value = mock_response

        mock_upload.return_value = "https://cdn.example.com/path/file.png"

        result = upload_image_from_url(
            "https://source.example.com/image.png", "path/file.png"
        )

        mock_httpx_get.assert_called_once_with(
            "https://source.example.com/image.png", timeout=30.0
        )
        mock_response.raise_for_status.assert_called_once()
        mock_upload.assert_called_once_with(b"downloaded image bytes", "path/file.png")
        assert result == "https://cdn.example.com/path/file.png"

    @patch("app.utils.oss.upload_image_to_oss")
    @patch("app.utils.oss.httpx.get")
    def test_auto_generates_key_when_none(self, mock_httpx_get, mock_upload):
        """Should auto-generate object_key when not provided."""
        mock_response = MagicMock()
        mock_response.content = b"image data"
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_httpx_get.return_value = mock_response

        mock_upload.return_value = "https://cdn.example.com/ai-generated/20250101/uuid.jpeg"

        result = upload_image_from_url("https://source.example.com/image.jpg")

        # Verify upload was called with an auto-generated key
        call_args = mock_upload.call_args
        generated_key = call_args[0][1]
        assert generated_key.startswith("ai-generated/")
        assert generated_key.endswith((".jpeg", ".jpg", ".jpe"))

    @patch("app.utils.oss.httpx.get")
    def test_raises_on_download_failure(self, mock_httpx_get):
        """Should raise when download fails."""
        import httpx

        mock_httpx_get.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )

        with pytest.raises(httpx.HTTPStatusError):
            upload_image_from_url("https://source.example.com/missing.png")


class TestUploadImageFromBytes:
    """Tests for upload_image_from_bytes."""

    @patch("app.utils.oss.upload_image_to_oss")
    def test_uploads_with_explicit_key(self, mock_upload):
        """Should upload bytes with the given object key."""
        mock_upload.return_value = "https://cdn.example.com/custom/key.png"

        result = upload_image_from_bytes(
            b"raw image data", "image/png", "custom/key.png"
        )

        mock_upload.assert_called_once_with(b"raw image data", "custom/key.png")
        assert result == "https://cdn.example.com/custom/key.png"

    @patch("app.utils.oss.upload_image_to_oss")
    def test_auto_generates_key_when_none(self, mock_upload):
        """Should auto-generate object_key when not provided."""
        mock_upload.return_value = "https://cdn.example.com/ai-generated/20250101/uuid.png"

        upload_image_from_bytes(b"raw image data", "image/png")

        call_args = mock_upload.call_args
        generated_key = call_args[0][1]
        assert generated_key.startswith("ai-generated/")
        assert generated_key.endswith(".png")

    @patch("app.utils.oss.upload_image_to_oss")
    def test_uses_content_type_for_extension(self, mock_upload):
        """Should derive extension from content_type."""
        mock_upload.return_value = "https://cdn.example.com/ai-generated/20250101/uuid.webp"

        upload_image_from_bytes(b"webp data", "image/webp")

        call_args = mock_upload.call_args
        generated_key = call_args[0][1]
        assert generated_key.endswith(".webp")


class TestUploadImageFromBase64:
    """Tests for upload_image_from_base64."""

    @patch("app.utils.oss.upload_image_to_oss")
    def test_uploads_raw_base64(self, mock_upload):
        """Should decode raw base64 and upload."""
        mock_upload.return_value = "https://cdn.example.com/ai-generated/20250101/uuid.png"
        raw_data = b"fake image content"
        b64_str = base64.b64encode(raw_data).decode()

        upload_image_from_base64(b64_str, "custom/key.png")

        mock_upload.assert_called_once_with(raw_data, "custom/key.png")

    @patch("app.utils.oss.upload_image_to_oss")
    def test_strips_data_uri_prefix(self, mock_upload):
        """Should strip 'data:image/png;base64,' prefix."""
        mock_upload.return_value = "https://cdn.example.com/ai-generated/20250101/uuid.png"
        raw_data = b"fake png content"
        b64_str = f"data:image/png;base64,{base64.b64encode(raw_data).decode()}"

        upload_image_from_base64(b64_str, "custom/key.png")

        mock_upload.assert_called_once_with(raw_data, "custom/key.png")

    @patch("app.utils.oss.upload_image_to_oss")
    def test_extracts_content_type_from_data_uri(self, mock_upload):
        """Should extract content type from data URI for extension."""
        mock_upload.return_value = "https://cdn.example.com/ai-generated/20250101/uuid.jpeg"
        raw_data = b"fake jpeg content"
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(raw_data).decode()}"

        upload_image_from_base64(b64_str)

        call_args = mock_upload.call_args
        generated_key = call_args[0][1]
        assert generated_key.startswith("ai-generated/")
        assert generated_key.endswith((".jpeg", ".jpg", ".jpe"))

    @patch("app.utils.oss.upload_image_to_oss")
    def test_auto_generates_key_when_none(self, mock_upload):
        """Should auto-generate object_key when not provided."""
        mock_upload.return_value = "https://cdn.example.com/ai-generated/20250101/uuid.png"
        raw_data = b"image bytes"
        b64_str = base64.b64encode(raw_data).decode()

        upload_image_from_base64(b64_str)

        call_args = mock_upload.call_args
        generated_key = call_args[0][1]
        assert generated_key.startswith("ai-generated/")
        assert generated_key.endswith(".png")

    def test_raises_on_invalid_base64(self):
        """Should raise ValueError for invalid base64 data."""
        with pytest.raises(ValueError, match="Invalid base64 data"):
            upload_image_from_base64("not-valid-base64!!!")
