
from typing import List
from sqlalchemy.future import select

import uuid

from cor_lab.database.models import User, Verification
from cor_lab.repository.password_generator import generate_password
from cor_lab.repository import cor_id as repository_cor_id
from cor_lab.schemas import (
    NewUserRegistration,
    PasswordGeneratorSettings,
    UserModel,
)
from cor_lab.services.auth import auth_service
from cor_lab.services import roles as role_check
from loguru import logger
from cor_lab.services.cipher import (
    generate_aes_key,
    encrypt_user_key
)
from cor_lab.services.email import (
    send_email_code_with_temp_pass,
)
from sqlalchemy.exc import NoResultFound

from sqlalchemy.ext.asyncio import AsyncSession
from cor_lab.config.config import settings


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """
    Асинхронно получает пользователя по его email.

    """
    email_lower = email.lower()
    stmt = select(User).where(User.email.ilike(email_lower))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user


async def get_user_by_uuid(uuid: str, db: AsyncSession) -> User | None:
    """
    Асинхронно получает пользователя по его UUID.

    """
    stmt = select(User).where(User.id == uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user


async def get_user_by_corid(cor_id: str, db: AsyncSession) -> User | None:
    """
    Асинхронно получает пользователя по его Cor ID.

    """
    stmt = select(User).where(User.cor_id == cor_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user


async def create_user(body: UserModel, db: AsyncSession) -> User:
    """
    Асинхронно создает нового юзера в базе данных.

    """

    new_user = User(**body.model_dump())
    new_user.id = str(uuid.uuid4())

    new_user.unique_cipher_key = await generate_aes_key()  # ->bytes
    new_user.unique_cipher_key = await encrypt_user_key(new_user.unique_cipher_key)


    try:
        db.add(new_user)

        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        await db.rollback()
        raise e



async def get_users(skip: int, limit: int, db: AsyncSession) -> list[User]:
    """
    Асинхронно возвращает список всех пользователей базы данных.

    """
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return list(users)



async def write_verification_code(
    email: str, db: AsyncSession, verification_code: int
) -> None:
    """
    Асинхронно записывает или обновляет верификационный код для указанного email.

    """
    stmt = select(Verification).where(Verification.email == email)
    result = await db.execute(stmt)
    verification_record = result.scalar_one_or_none()

    if verification_record:
        verification_record.verification_code = verification_code
        try:
            await db.commit()
            logger.debug("Обновлен код верификации в существующей записи")
        except Exception as e:
            await db.rollback()
            raise e
    else:
        verification_record = Verification(
            email=email, verification_code=verification_code
        )
        try:
            db.add(verification_record)
            await db.commit()
            await db.refresh(verification_record)
            logger.debug("Создана новая запись верификации")
        except Exception as e:
            await db.rollback()
            raise e


async def verify_verification_code(
    email: str, db: AsyncSession, verification_code: int
) -> bool:
    """
    Асинхронно проверяет код верификации для указанного e-mail.

    """
    try:
        stmt = select(Verification).where(Verification.email == email)
        result = await db.execute(stmt)
        verification_record = result.scalar_one_or_none()

        if (
            verification_record
            and verification_record.verification_code == verification_code
        ):
            verification_record.email_confirmation = True
            await db.commit()
            return True
        else:
            return False
    except Exception as e:
        raise e


async def change_user_password(email: str, password: str, db: AsyncSession) -> None:
    """
    Асинхронно изменяет пользовательский пароль.
    """
    user = await get_user_by_email(email, db)
    if user:
        hashed_password = auth_service.get_password_hash(password)
        user.password = hashed_password
        try:
            await db.commit()
            logger.debug("Password has changed")
        except Exception as e:
            await db.rollback()
            raise e
    else:
        logger.warning(f"User with email {email} not found during password change.")


async def change_user_email(email: str, current_user, db: AsyncSession) -> None:
    """
    Асинхронно изменяет email пользователя.
    """
    current_user.email = email
    try:
        await db.commit()
        logger.debug("Email has changed")
    except Exception as e:
        await db.rollback()
        raise e


async def add_user_backup_email(
    email: str, current_user: User, db: AsyncSession
) -> None:
    """
    Асинхронно добавляет резервный email пользователю.
    """
    current_user.backup_email = email
    try:
        await db.commit()
        logger.debug("Backup email has added")
    except Exception as e:
        await db.rollback()
        raise e


async def delete_user_by_email(db: AsyncSession, email: str):
    """
    Асинхронно удаляет пользователя по его email.
    """
    try:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one()

        await db.delete(user)
        await db.commit()
    except NoResultFound:
        print("Пользователя не найдено.")
    except Exception as e:
        await db.rollback()
        print(f"Произошла ошибка при удалении пользователя: {e}")



async def get_user_roles(email: str, db: AsyncSession) -> List[str]:
    roles = []
    user = await get_user_by_email(email, db)

    if await role_check.admin_role_checker.is_admin(user=user):
        roles.append("admin")
    if await role_check.lawyer_role_checker.is_lawyer(user=user, db=db):
        roles.append("lawyer")
    if await role_check.cor_int_role_checker.is_cor_int(user=user):
        roles.append("cor-int")
    doctor = await role_check.doctor_role_checker.is_doctor(user=user, db=db)
    if doctor:
        roles.append("doctor")
    lab_assistant = await role_check.lab_assistant_role_checker.is_lab_assistant(
        user=user, db=db
    )
    if lab_assistant:
        roles.append("lab_assistant")
    energy_manager = await role_check.energy_manager_role_checker.is_energy_manager(
        user=user, db=db
    )
    if energy_manager:
        roles.append("energy_manager")
    if user.is_active:
        roles.append("active_user")
    return roles


async def register_new_user(db: AsyncSession, body: NewUserRegistration):
    """
    Асинхронно регистрирует нового пользователя как пациента и связывает его с врачом.
    """
    # Генерируем временный пароль
    password_settings = PasswordGeneratorSettings()
    temp_password = generate_password(password_settings)
    hashed_password = auth_service.get_password_hash(temp_password)

    user_signup_data = UserModel(
        email=body.email,
        password=temp_password,
        birth=body.birth_date.year,
        user_sex=body.sex,
    )
    hashed_password = auth_service.get_password_hash(temp_password)
    user_signup_data.password = hashed_password

    new_user = await create_user(user_signup_data, db)

    await db.flush()

    await repository_cor_id.create_new_corid(new_user, db)
    await db.commit()

    await send_email_code_with_temp_pass(email=body.email, temp_pass=temp_password)
