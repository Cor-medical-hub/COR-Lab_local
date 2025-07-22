from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cor_lab.database import db
from cor_lab.database.models import Doctor, Doctor_Status, Lawyer, User, LabAssistant
from cor_lab.services.auth import auth_service
from cor_lab.config.config import settings


class AdminAccess:
    def __init__(self, email):
        self.email = email

    async def __call__(self, user: User = Depends(auth_service.get_current_user)):
        if not user.email in settings.admin_accounts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden operation"
            )


class LawyerAccess:
    def __init__(self, email):
        self.email = email

    async def __call__(
        self,
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(db.get_db),
    ):
        has_access = False
        if user.email in settings.admin_accounts:
            has_access = True
        if user.email in settings.lawyer_accounts:
            has_access = True

        query = select(Lawyer).where(Lawyer.lawyer_cor_id == user.cor_id)
        result = await db.execute(query)
        lawyer = result.scalar_one_or_none()
        if lawyer:
            has_access = True

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения этой операции.",
            )


class DoctorAccess:
    def __init__(self, email):
        self.email = email

    async def __call__(
        self,
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(db.get_db),
    ):
        query = select(Doctor).where(Doctor.doctor_id == user.cor_id)
        result = await db.execute(query)
        doctor = result.scalar_one_or_none()
        if not doctor or doctor.status != Doctor_Status.approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor access required and status is not approved",
            )
        return doctor


class LabAssistantOrDoctorAccess:
    def __init__(self, email):
        self.email = email

    async def __call__(
        self,
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(db.get_db),
    ):
        lab_assistant_query = select(LabAssistant).where(
            LabAssistant.lab_assistant_cor_id == user.cor_id
        )
        lab_assistant = await db.scalar(lab_assistant_query)

        if lab_assistant:
            return lab_assistant

        doctor_query = select(Doctor).where(Doctor.doctor_id == user.cor_id)
        doctor = await db.scalar(doctor_query)

        if doctor and doctor.status == Doctor_Status.approved:
            return doctor

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права лаборанта или одобренного доктора.",
        )


admin_access = AdminAccess([User.email])
lawyer_access = LawyerAccess([User.email])
doctor_access = DoctorAccess([User.email])
lab_assistant_or_doctor_access = LabAssistantOrDoctorAccess([User.email])
