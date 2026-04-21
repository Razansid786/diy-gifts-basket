"""
app/services/upload_service.py
──────────────────────────────
File upload service using Supabase Storage (FR20).

Handles uploading gift-tag images to a Supabase Storage bucket
and returning the public URL.
"""

import uuid
from typing import Optional

from fastapi import UploadFile

from app.core.config import get_settings


class UploadService:
    """Handles file uploads to Supabase Storage."""

    BUCKET_NAME = "gift-tags"
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

    async def upload_gift_tag(self, file: UploadFile) -> str:
        """
        Upload a gift-tag image to Supabase Storage (FR20).

        Parameters
        ----------
        file : UploadFile
            The uploaded image file.

        Returns
        -------
        str
            Public URL of the uploaded file.

        Raises
        ------
        ValueError
            If the file type is not allowed or exceeds the size limit.
        """
        # Validate file type
        if file.content_type not in self.ALLOWED_TYPES:
            raise ValueError(
                f"File type '{file.content_type}' not allowed. "
                f"Accepted types: {', '.join(self.ALLOWED_TYPES)}"
            )

        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > self.MAX_SIZE_BYTES:
            raise ValueError(
                f"File too large. Maximum size is {self.MAX_SIZE_BYTES // (1024*1024)} MB."
            )

        # Generate a unique filename
        extension = file.filename.split(".")[-1] if file.filename else "png"
        filename = f"{uuid.uuid4().hex}.{extension}"
        file_path = f"tags/{filename}"

        settings = get_settings()

        # If Supabase credentials are configured, upload to Supabase Storage
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
            try:
                from supabase import create_client
                supabase = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY,
                )
                supabase.storage.from_(self.BUCKET_NAME).upload(
                    path=file_path,
                    file=content,
                    file_options={"content-type": file.content_type},
                )
                # Build public URL
                public_url = (
                    f"{settings.SUPABASE_URL}/storage/v1/object/public/"
                    f"{self.BUCKET_NAME}/{file_path}"
                )
                return public_url

            except Exception as e:
                # Log the error and fall back to placeholder
                print(f"[UploadService] Supabase upload failed: {e}")

        # Fallback: return a placeholder URL (useful during development)
        return f"https://placeholder.local/uploads/{file_path}"
