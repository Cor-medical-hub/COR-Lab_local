from typing import Dict, List
from fastapi import APIRouter, Body, HTTPException, Depends, Response, status
from cor_lab.database.db import get_db
from cor_lab.repository import lawyer
from cor_lab.repository.doctor import create_doctor, create_doctor_service
from cor_lab.repository.lawyer import get_doctor
from cor_lab.services.websocket_events_manager import websocket_events_manager
from cor_lab.services.auth import auth_service
from cor_lab.database.models import Doctor_Status, User
from cor_lab.services.access import admin_access
from cor_lab.schemas import (
    CertificateResponse,
    ClinicAffiliationResponse,
    DiplomaResponse,
    DoctorCreate,
    DoctorCreateResponse,
    DoctorWithRelationsResponse,
    FullUserInfoResponse,
    NewUserRegistration,
    UserDataResponse,
    UserDb,
    UserDoctorsDataResponseForAdmin,
    UserRolesResponseForAdmin,
)
from cor_lab.repository import person
from pydantic import EmailStr
from cor_lab.database.redis_db import redis_client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from loguru import logger

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/get_all", response_model=List[UserDb], dependencies=[Depends(admin_access)]
)
async def get_all_users(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Get a list of users. / Получение списка всех пользователей**\n
    This route allows to get a list of pagination-aware users.
    Level of Access:
    - Admin
    :param skip: int: Number of users to skip.
    :param limit: int: Maximum number of users to return.
    :param current_user: User: Current authenticated user (for dependency injection).
    :param db: AsyncSession: Database session.
    :return: List of users with their last activity.
    :rtype: List[UserDb]
    """

    list_users = await person.get_users(skip, limit, db)
    users_list_with_activity = []

    for user in list_users:
        oid = str(user.id)
        last_active = None
        if await redis_client.exists(oid):
            users_last_activity = await redis_client.get(oid)
            user_response = UserDb(
                id=user.id,
                cor_id=user.cor_id,
                email=user.email,
                user_sex=user.user_sex,
                birth=user.birth,
                created_at=user.created_at,
                last_active=users_last_activity,
            )
        else:
            user_response = UserDb(
                id=user.id,
                cor_id=user.cor_id,
                email=user.email,
                user_sex=user.user_sex,
                birth=user.birth,
                created_at=user.created_at,
            )

        users_list_with_activity.append(user_response)

    return users_list_with_activity


@router.get(
    "/get_user_info/{user_cor_id}",
    response_model=FullUserInfoResponse,
    dependencies=[Depends(admin_access)],
)
async def get_all_user_info(
    user_cor_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Get a list of user's info. / Получение всей информации по пользователю**\n
    Level of Access:
    - Admin
    """
    full_user_data = {}

    user = await person.get_user_by_corid(db=db, cor_id=user_cor_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")

    last_active = None
    if await redis_client.exists(str(user.id)):
        users_last_activity_str = await redis_client.get(str(user.id))
        try:
            last_active = users_last_activity_str
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing last_active from Redis: {e}")
            last_active = None

    full_user_data["user_info"] = UserDb(
        id=user.id,
        cor_id=user.cor_id,
        email=user.email,
        user_sex=user.user_sex,
        birth=user.birth,
        created_at=user.created_at,
        last_active=last_active,
    )

    user_roles = await person.get_user_roles(email=user.email, db=db)
    if user_roles:
        full_user_data["user_roles"] = user_roles

    doctor = await lawyer.get_all_doctor_info(doctor_id=user.cor_id, db=db)
    if doctor:
        doctor_response = DoctorWithRelationsResponse(
            id=doctor.id,
            doctor_id=doctor.doctor_id,
            phone_number=doctor.phone_number,
            first_name=doctor.first_name,
            middle_name=doctor.middle_name,
            doctors_photo=(
                f"/doctors/{doctor.doctor_id}/photo" if doctor.doctors_photo else None
            ),
            last_name=doctor.last_name,
            place_of_registration=doctor.place_of_registration,
            passport_code=doctor.passport_code,
            taxpayer_identification_number=doctor.taxpayer_identification_number,
            scientific_degree=doctor.scientific_degree,
            date_of_last_attestation=doctor.date_of_last_attestation,
            status=doctor.status,
            diplomas=[
                DiplomaResponse(
                    id=diploma.id,
                    date=diploma.date,
                    series=diploma.series,
                    number=diploma.number,
                    university=diploma.university,
                    file_data=f"/diplomas/{diploma.id}" if diploma.file_data else None,
                )
                for diploma in doctor.diplomas
            ],
            certificates=[
                CertificateResponse(
                    id=certificate.id,
                    date=certificate.date,
                    series=certificate.series,
                    number=certificate.number,
                    university=certificate.university,
                    file_data=(
                        f"/certificates/{certificate.id}"
                        if certificate.file_data
                        else None
                    ),
                )
                for certificate in doctor.certificates
            ],
            clinic_affiliations=[
                ClinicAffiliationResponse(
                    id=affiliation.id,
                    clinic_name=affiliation.clinic_name,
                    department=affiliation.department,
                    position=affiliation.position,
                    specialty=affiliation.specialty,
                )
                for affiliation in doctor.clinic_affiliations
            ],
        )
        full_user_data["doctor_info"] = doctor_response

    return full_user_data


@router.get(
    "/get_user_info/{user_cor_id}/user-data",
    response_model=UserDataResponse,
    dependencies=[Depends(admin_access)],
)
async def get_user_data_info(
    user_cor_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Get a list of user's info. / Получение всей информации по пользователю**\n
    Level of Access:
    - Admin
    """
    user_data = {}

    user = await person.get_user_by_corid(db=db, cor_id=user_cor_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")

    last_active = None
    if await redis_client.exists(str(user.id)):
        users_last_activity_str = await redis_client.get(str(user.id))
        try:
            last_active = users_last_activity_str
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing last_active from Redis: {e}")
            last_active = None

    user_data["user_info"] = UserDb(
        id=user.id,
        cor_id=user.cor_id,
        email=user.email,
        user_sex=user.user_sex,
        birth=user.birth,
        created_at=user.created_at,
        last_active=last_active,
    )

    return user_data


@router.get(
    "/get_user_info/{user_cor_id}/user-roles",
    response_model=UserRolesResponseForAdmin,
    dependencies=[Depends(admin_access)],
)
async def get_user_roles_info(
    user_cor_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Get a list of user's info. / Получение всей информации по пользователю**\n
    Level of Access:
    - Admin
    """
    user_data = {}

    user = await person.get_user_by_corid(db=db, cor_id=user_cor_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")

    user_roles = await person.get_user_roles(email=user.email, db=db)
    if user_roles:
        user_data["user_roles"] = user_roles

    return user_data


@router.get(
    "/get_user_info/{user_cor_id}/doctors-data",
    response_model=UserDoctorsDataResponseForAdmin,
    dependencies=[Depends(admin_access)],
)
async def get_user_doctors_info(
    user_cor_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **Get a list of user's info. / Получение всей информации по пользователю**\n
    Level of Access:
    - Admin
    """
    user_data = {}

    user = await person.get_user_by_corid(db=db, cor_id=user_cor_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")

    doctor = await lawyer.get_all_doctor_info(doctor_id=user.cor_id, db=db)
    if doctor:
        doctor_response = DoctorWithRelationsResponse(
            id=doctor.id,
            doctor_id=doctor.doctor_id,
            work_email=doctor.work_email,
            phone_number=doctor.phone_number,
            first_name=doctor.first_name,
            middle_name=doctor.middle_name,
            doctors_photo=(
                f"/doctors/{doctor.doctor_id}/photo" if doctor.doctors_photo else None
            ),
            last_name=doctor.last_name,
            place_of_registration=doctor.place_of_registration,
            passport_code=doctor.passport_code,
            taxpayer_identification_number=doctor.taxpayer_identification_number,
            scientific_degree=doctor.scientific_degree,
            date_of_last_attestation=doctor.date_of_last_attestation,
            status=doctor.status,
            diplomas=[
                DiplomaResponse(
                    id=diploma.id,
                    date=diploma.date,
                    series=diploma.series,
                    number=diploma.number,
                    university=diploma.university,
                    file_data=f"/diplomas/{diploma.id}" if diploma.file_data else None,
                )
                for diploma in doctor.diplomas
            ],
            certificates=[
                CertificateResponse(
                    id=certificate.id,
                    date=certificate.date,
                    series=certificate.series,
                    number=certificate.number,
                    university=certificate.university,
                    file_data=(
                        f"/certificates/{certificate.id}"
                        if certificate.file_data
                        else None
                    ),
                )
                for certificate in doctor.certificates
            ],
            clinic_affiliations=[
                ClinicAffiliationResponse(
                    id=affiliation.id,
                    clinic_name=affiliation.clinic_name,
                    department=affiliation.department,
                    position=affiliation.position,
                    specialty=affiliation.specialty,
                )
                for affiliation in doctor.clinic_affiliations
            ],
        )
        user_data["doctor_info"] = doctor_response

    return user_data


@router.delete("/{email}", dependencies=[Depends(admin_access)])
async def delete_user(email: EmailStr, db: AsyncSession = Depends(get_db)):
    """
        **Delete user by email. / Удаление пользователя по имейлу**\n

    =
    """
    user = await person.get_user_by_email(email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    else:
        await person.delete_user_by_email(db=db, email=email)
        return {"message": f" user {email} - was deleted"}


@router.patch("/deactivate/{email}", dependencies=[Depends(admin_access)])
async def deactivate_user(email: EmailStr, db: AsyncSession = Depends(get_db)):
    """
    **Deactivate user by email. / Деактивация аккаунта пользователя**\n

    This route allows to deactivate a user account by their email.

    :param email: EmailStr: Email of the user to deactivate.

    :param db: AsyncSession: Database Session.

    :return: Message about successful deactivation.

    :rtype: dict
    """
    user = await person.get_user_by_email(email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not user.is_active:
        return {"message": f"The {user.email} account is already deactivated"}
    else:
        await person.deactivate_user(email, db)
        return {"message": f"{user.email} - account is deactivated"}



@router.post(
    "/signup_as_doctor",
    response_model=DoctorCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_access)],
)
async def signup_user_as_doctor(
    user_cor_id: str,
    doctor_data: DoctorCreate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    **Создание врача со всеми связанными данными**\n
    Этот маршрут позволяет создать врача вместе с дипломами, сертификатами и привязками к клиникам.
    Уровень доступа:
    - Текущий авторизованный пользователь
    :param doctor_data: str: Данные для создания врача в формате JSON.
    :param db: AsyncSession: Сессия базы данных.
    :return: Созданный врач.
    :rtype: DoctorResponse
    """

    exist_doctor = await get_doctor(db=db, doctor_id=user_cor_id)
    if exist_doctor:
        logger.debug(f"{user_cor_id} doctor already exist")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Doctor account already exists"
        )
    user = await person.get_user_by_corid(db=db, cor_id=user_cor_id)
    if not user:
        logger.debug(f"User not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        doctor = await create_doctor(
            doctor_data=doctor_data,
            db=db,
            user=user,
        )
        cer, dip, clin = await create_doctor_service(
            doctor_data=doctor_data, db=db, doctor=doctor
        )

        await lawyer.approve_doctor(doctor=doctor, db=db, status=Doctor_Status.approved)
    except IntegrityError as e:
        logger.error(f"Database integrity error: {e}")
        await db.rollback()
        detail = "Database error occurred. Please check the data for duplicates or invalid entries."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during doctor creation.",
        )
    # Сериализуем ответ
    doctor_response = DoctorCreateResponse(
        id=doctor.id,
        doctor_cor_id=doctor.doctor_id,
        phone_number=doctor.phone_number,
        first_name=doctor.first_name,
        middle_name=doctor.middle_name,
        last_name=doctor.last_name,
        scientific_degree=doctor.scientific_degree,
        date_of_last_attestation=doctor.date_of_last_attestation,
        status=doctor.status,
        diploma_id=dip,
        certificates_id=cer,
        clinic_affiliations_id=clin,
        place_of_registration=doctor.place_of_registration,
        passport_code=doctor.passport_code,
        taxpayer_identification_number=doctor.taxpayer_identification_number,
    )

    return doctor_response


@router.patch("/asign_doctor_status/{doctor_id}", dependencies=[Depends(admin_access)])
async def assign_status(
    doctor_id: str,
    doctor_status: Doctor_Status,
    db: AsyncSession = Depends(get_db),
):
    """
    **Assign a doctor_status to a doctor by doctor_id. / Применение нового статуса доктора (подтвержден / на рассмотрении)**\n

    :param doctor_id: str: doctor_id of the user to whom you want to assign the status.

    :param doctor_status: DoctorStatus: The selected doctor_status for the assignment.

    :param db: AsyncSession: Database Session.

    :return: Message about successful status change.

    :rtype: dict
    """
    doctor = await lawyer.get_doctor(doctor_id=doctor_id, db=db)

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found"
        )

    if doctor_status == doctor.status:
        return {"message": "The account status has already been assigned"}
    else:
        await lawyer.approve_doctor(doctor=doctor, db=db, status=doctor_status)
        return {
            "message": f"{doctor.first_name} {doctor.last_name}'s status - {doctor_status.value}"
        }


@router.post(
    "/register_new_user",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_access)],
)
async def register_new_user(
    body: NewUserRegistration, db: AsyncSession = Depends(get_db)
):
    """
    Создает нового пользователя с временным паролем
    """

    if body:
        new_user_info = body
        exist_user = await person.get_user_by_email(new_user_info.email, db)
        if exist_user:
            logger.debug(f"{new_user_info.email} user already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
            )
        new_user = await person.register_new_user(db=db, body=new_user_info)
        return {"message": f"Новый пользователь {body.email} успешно зарегистрирован."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректные данные регистрации пользователя.",
        )


@router.get(
    "/ws_connections",
    summary="Получить список активных WebSocket-соединений",
    response_model=List[Dict],
    dependencies=[Depends(admin_access)],
)
async def get_ws_connections():
    """
    Возвращает список всех активных WebSocket-соединений, включая их ID и информацию о клиенте.
    Требуются права администратора.
    """
    return websocket_events_manager.get_active_connection_info()


@router.delete(
    "/ws_connections/{connection_id}",
    summary="Отключить конкретное WebSocket-соединение",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_access)],
)
async def disconnect_specific_ws_connection(connection_id: str):
    """
    Отключает конкретное WebSocket-соединение по его ID.
    Требуются права администратора.
    """
    await websocket_events_manager.disconnect(connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/ws_connections/",
    summary="Отключить все активные WebSocket-соединения",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_access)],
)
async def disconnect_all_ws_connections():
    """
    Отключает все активные WebSocket-соединения.
    Требуются права администратора.
    """
    await websocket_events_manager.disconnect_all()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
