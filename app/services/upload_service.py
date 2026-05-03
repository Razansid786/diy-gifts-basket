
import uuid
from typing import Optional

from fastapi import UploadFile

from app.core.config import get_settings

class UploadService:

    BUCKET_NAME = "gift-tags"
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_SIZE_BYTES = 5 * 1024 * 1024

    async def upload_gift_tag(self, file: UploadFile) -> str:

        if file.content_type not in self.ALLOWED_TYPES:
            raise ValueError(
                f"File type '{file.content_type}' not allowed. "
                f"Accepted types: {', '.join(self.ALLOWED_TYPES)}"
            )

        content = await file.read()

        if len(content) > self.MAX_SIZE_BYTES:
            raise ValueError(
                f"File too large. Maximum size is {self.MAX_SIZE_BYTES // (1024*1024)} MB."
            )

        extension = file.filename.split(".")[-1] if file.filename else "png"
        filename = f"{uuid.uuid4().hex}.{extension}"
        file_path = f"tags/{filename}"

        settings = get_settings()

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

                public_url = (
                    f"{settings.SUPABASE_URL}/storage/v1/object/public/"
                    f"{self.BUCKET_NAME}/{file_path}"
                )
                return public_url

            except Exception as e:

                print(f"[UploadService] Supabase upload failed: {e}")

        import os
        upload_dir = os.path.join(os.getcwd(), "frontend", "public", "images", "uploads")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)

        local_path = os.path.join(upload_dir, filename)
        with open(local_path, "wb") as f:
            f.write(content)

        return f"/images/uploads/{filename}"