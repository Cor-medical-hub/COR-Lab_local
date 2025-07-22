from fastapi import UploadFile, HTTPException, status

from cor_lab.services.image_validation import ALLOWED_IMAGE_TYPES, validate_image_file


# Константы для валидации PDF
ALLOWED_PDF_TYPES = {"application/pdf"}
MAX_PDF_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def validate_pdf_file(file: UploadFile):

    if file.size > MAX_PDF_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл PDF слишком большой. Максимальный размер: {MAX_PDF_FILE_SIZE // (1024 * 1024)}MB",
        )

    if file.content_type not in ALLOWED_PDF_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Файл должен быть PDF",
        )

    file_header = await file.read(4)
    await file.seek(0)
    if file_header != b"%PDF":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Файл не является корректным PDF",
        )

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext != "pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Неподдерживаемое расширение файла - {file_ext}. Разрешен только 'pdf'",
        )

    return file


async def validate_document_file(file: UploadFile):
    try:
        await validate_image_file(file)
        return file
    except HTTPException as image_err:
        try:
            await validate_pdf_file(file)
            return file
        except HTTPException as pdf_err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый формат файла. Разрешены: {', '.join(ALLOWED_IMAGE_TYPES)} и PDF. Ошибки: изображение - '{image_err.detail}', PDF - '{pdf_err.detail}'",
            )
