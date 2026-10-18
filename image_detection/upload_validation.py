"""Small, dependency-light validation helpers for uploaded crop images."""

import os
import uuid

from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image_upload(filename, content_length, max_bytes):
    """Return a safe extension or a short validation error."""
    safe_name = secure_filename(filename or "")
    if not safe_name or safe_name in {".", ".."}:
        return None, "A valid image filename is required."
    extension = os.path.splitext(safe_name)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return None, "Unsupported image format. Upload JPG, PNG, or WEBP."
    if content_length is not None and content_length > max_bytes:
        return None, "Image exceeds the maximum upload size."
    return extension, None


def unique_upload_path(upload_dir, extension):
    """Create a collision-resistant path without trusting the client filename."""
    return os.path.join(upload_dir, f"{uuid.uuid4().hex}{extension}")
