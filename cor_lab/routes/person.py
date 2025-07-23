from fastapi import APIRouter,  HTTPException, Depends, UploadFile, status
from datetime import datetime, timedelta, timezone
from cor_lab.database.db import get_db
from cor_lab.services import redis_service
from cor_lab.services.websocket_events_manager import websocket_events_manager
from cor_lab.services.auth import auth_service
from cor_lab.services.cipher import decrypt_data, decrypt_user_key
from cor_lab.services.image_validation import validate_image_file
from cor_lab.services.qr_code import generate_qr_code
from cor_lab.services.recovery_file import generate_recovery_file
from cor_lab.services.email import send_email_code_with_qr
from cor_lab.database.models import User
from loguru import logger
from cor_lab.schemas import (
    DeleteMyAccount,
    EmailSchema,
    ChangePasswordModel,
    ChangeMyPasswordModel,
    ProfileCreate,
    ProfileResponse,
    UserSessionResponseModel,
)
from cor_lab.repository import person
from cor_lab.repository import cor_id as repository_cor_id
from cor_lab.repository import user_session as repository_session
from cor_lab.config.config import settings
from pydantic import EmailStr
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

import base64
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter

router = APIRouter(prefix="/user", tags=["User"])


@router.get(
    "/my_core_id",
    
)
async def read_cor_id(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Просмотр своего COR-id** \n

    """

    cor_id = await repository_cor_id.get_cor_id(current_user, db)
    if cor_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="COR-Id not found"
        )
    return cor_id


@router.get(
    "/my_core_id_qr",
    
)
async def get_cor_id_qr(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Просмотр своего QR COR-id** \n
    """
    cor_id = await repository_cor_id.get_cor_id(current_user, db)
    if cor_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="COR-Id not found"
        )
    cor_id_qr_bytes = generate_qr_code(cor_id)

    # Конвертация QR-кода в Base64
    encoded_qr = base64.b64encode(cor_id_qr_bytes).decode("utf-8")
    qr_code_data_url = f"data:image/png;base64,{encoded_qr}"

    return JSONResponse(content={"qr_code_url": qr_code_data_url})


@router.get("/get_email")
async def get_user_email(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Получения имейла авторизированного пользователя**\n
    Level of Access:
    - Current authorized user
    """

    email = current_user.email
    return {"users email": email}


@router.patch("/change_email")
async def change_email(
    body: EmailSchema,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Смена имейла авторизированного пользователя** \n
    """
    existing_email = await person.get_user_by_email(body.email, db)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exist"
        )
    user = await person.get_user_by_email(current_user.email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    else:
        if body.email:
            await person.change_user_email(body.email, user, db)
            logger.debug(f"{current_user.id} - changed his email to {body.email}")
            return {
                "message": f"User '{current_user.id}' changed his email to {body.email}"
            }
        else:
            logger.warning("Incorrect email input provided for user email change.")
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Incorrect email input",
            )


   
@router.patch("/change_password")
async def change_password(
    body: ChangePasswordModel,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Смена пароля в сценарии "Забыли пароль"** \n
    """

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    else:
        if body.password:
            await person.change_user_password(current_user.email, body.password, db)
            logger.debug(f"{current_user.email} - changed his password")
            return {"message": f"User '{current_user.email}' changed his password"}
        else:
            logger.warning(
                "Incorrect password input provided for user password change."
            )
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Incorrect password input",
            )


@router.patch("/change_my_password")
async def change_my_password(
    body: ChangeMyPasswordModel,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Смена пароля в сценарии "Изменить свой пароль"** \n
    """

    if not auth_service.verify_password(body.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid old password"
        )
    else:
        if body.new_password:
            await person.change_user_password(current_user.email, body.new_password, db)
            logger.debug(f"{current_user.email} - changed his password")
            return {"message": f"User '{current_user.email}' changed his password"}
        else:
            logger.warning(
                "Incorrect new password input provided for user password change."
            )
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Incorrect new password input",
            )


@router.delete("/delete_my_account")
async def delete_my_account(
    body: DeleteMyAccount,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    **Delete user account and all data. / Удаление пользовательского аккаунта и всех его данных**\n
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    else:
        if auth_service.verify_password(body.password, current_user.password):
            await person.delete_user_by_email(db=db, email=current_user.email)
            logger.info(f"Account for user {current_user.email} was deleted")
            return {"message": f" user {current_user.email} - was deleted"}
        else:
            return {"message": f"Password incorrect"}


@router.get(
    "/sessions/all",
    response_model=List[UserSessionResponseModel],
    
)
async def read_sessions(
    skip: int = 0,
    limit: int = 150,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Get a list of user_sessions. / Получение всех сессий пользователя** \n

    :param skip: The number of sessions to skip (for pagination). Default is 0.
    :type skip: int
    :param limit: The maximum number of sessions to retrieve. Default is 50.
    :type limit: int
    :param db: The database session. Dependency on get_db.
    :type db: AsyncSession, optional
    :return: A list of UserSessionModel objects representing the sessions.
    :rtype: List[UserSessionResponseModel]
    """
    try:
        sessions_from_db = await repository_session.get_all_user_sessions(
            db, current_user.cor_id, skip, limit
        )
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    response_sessions = []
    for session in sessions_from_db:
       
        session_response = UserSessionResponseModel(
            id=session.id,
            user_id=session.user_id,
            device_type=session.device_type,
            device_info=session.device_info,
            ip_address=session.ip_address,
            device_os=session.device_os,
            created_at=session.created_at,
            updated_at=session.updated_at,
            jti=session.jti
        )
        response_sessions.append(session_response)

    return response_sessions


@router.get(
    "/sessions/{session_id}",
    response_model=UserSessionResponseModel,
    
)
async def read_session_info(
    session_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Get a specific session by ID. / Получение данных одной конкретной сессии пользователя** \n

    :param session_id: The ID of the session.
    :type session_id: str
    :param db: The database session. Dependency on get_db.
    :type db: AsyncSession, optional
    :return: The UserSessionModel object representing the session.
    :rtype: UserSessionResponseModel
    :raises HTTPException 404: If the session with the specified ID does not exist.
    """
    user_session = await repository_session.get_session_by_id(
        current_user, db, session_id
    )
    if user_session is None:
        logger.exception(
            f"Session with ID '{session_id}' not found for user '{current_user.id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    response_data = {
        "id": user_session.id,
        "user_id": user_session.user_id,
        "device_type": user_session.device_type,
        "device_info": user_session.device_info,
        "ip_address": user_session.ip_address,
        "device_os": user_session.device_os,
        "created_at": user_session.created_at,
        "updated_at": user_session.updated_at,
        "jti": user_session.jti
    }

    return UserSessionResponseModel(**response_data)


@router.delete("/sessions/{session_id}", response_model=UserSessionResponseModel)
async def remove_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    **Remove a session. / Удаление сессии** \n
    :param session_id: The ID of the session to remove.
    :type session_id: str
    :param db: The database session. Dependency on get_db.
    :type db: AsyncSession, optional
    :return: The removed UserSessionModel object representing the removed session.
    :rtype: UserSessionResponseModel
    :raises HTTPException 404: If the session with the specified ID does not exist.
    """
    session_to_revoke = await repository_session.get_session_by_id(
        db=db, session_id=session_id, user=current_user
    )
    if not session_to_revoke:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена."
        )

    if session_to_revoke.user_id != current_user.cor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете отозвать чужую сессию.",
        )
    if session_to_revoke.jti:
        blacklist_expires = timedelta(seconds=settings.access_token_expiration)
    await redis_service.add_jti_to_blacklist(session_to_revoke.jti, blacklist_expires)
    token = session_to_revoke.access_token
    session_token = await decrypt_data(
        encrypted_data=token,
        key=await decrypt_user_key(current_user.unique_cipher_key),
    )
    event_data = {
        "channel": "cor-erp-prod",
        "event_type": "token_blacklisted",
        "token": session_token,
        "reason": "Token explicitly revoked or logged out.",
        "timestamp": datetime.now(timezone.utc).timestamp(),
    }
    await websocket_events_manager.broadcast_event(event_data)

    session = await repository_session.delete_session(current_user, db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    return session

