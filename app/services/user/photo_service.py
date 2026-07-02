import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

# This directory will be mounted via docker-compose
UPLOAD_DIR = os.path.abspath(os.path.join(os.getcwd(), "uploads", "photos"))

# Magic Bytes for PNG and JPG
ALLOWED_MAGIC_BYTES = {
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG\r\n\x1a\n",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 5MB

class PhotoService:
    @staticmethod
    async def save_profile_photo(user_id: int, file: UploadFile) -> str:
        # 1. Enforce size limit (Read chunk to memory safely or check content-length if trusted, but reading is better)
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large. Max 5MB.")
            
        # 2. Validate Magic Bytes
        if len(content) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format.")
            
        detected_mime = None
        for mime, magic in ALLOWED_MAGIC_BYTES.items():
            if content.startswith(magic):
                detected_mime = mime
                break
                
        if not detected_mime:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Only JPG and PNG are allowed.")
            
        # Determine extension
        ext = ".jpg" if detected_mime == "image/jpeg" else ".png"
        
        # 3. Generate unique random filename
        filename = f"{uuid.uuid4().hex}{ext}"
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 4. Save outside web root, prevent directory traversal
        file_path = os.path.abspath(os.path.join(UPLOAD_DIR, filename))
        if not file_path.startswith(UPLOAD_DIR):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
            
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
            
        # Return URI or relative path
        # Assuming we serve photos under a specific route later, e.g., /static/photos/
        return f"/uploads/photos/{filename}"
