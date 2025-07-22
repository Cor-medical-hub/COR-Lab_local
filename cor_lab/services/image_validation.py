from fastapi import UploadFile, HTTPException, status
import imghdr

ALLOWED_IMAGE_TYPES = {"jpeg", "png", "jpg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


async def validate_image_file(file: UploadFile):
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE//(1024*1024)}MB",
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Файл должен быть изображением",
        )

    file_header = await file.read(32)
    await file.seek(0)
    image_type = imghdr.what(None, h=file_header)
    if image_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Неподдерживаемый тип изображения. Разрешены: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    file_ext = file.filename.split(".")[-1].lower()
    print(file_ext)
    if file_ext not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Неподдерживаемый формат файла - {file_ext}. Разрешены: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    return file
