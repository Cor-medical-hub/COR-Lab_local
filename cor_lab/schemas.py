from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    EmailStr,
    field_validator,

)
from typing import List, Literal, Optional, Union
from datetime import datetime

from cor_lab.database.models import (
    PatientClinicStatus,
    PatientStatus,
    Doctor_Status,
    MacroArchive,
    DecalcificationType,
    SampleType,
    MaterialType,
    UrgencyType,
    FixationType,
    StudyType,
    StainingType,
)
from datetime import date

# AUTH MODELS


class UserModel(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=20)
    birth: Optional[int] = Field(None, ge=1945, le=2100)
    user_sex: Optional[str] = Field(None, max_length=1)
    cor_id: Optional[str] = Field(None, max_length=15)

    @field_validator("user_sex")
    def user_sex_must_be_m_or_f(cls, v):
        if v not in ["M", "F"]:
            raise ValueError('user_sex must be "M" or "F"')
        return v


class UserDb(BaseModel):
    id: str
    cor_id: Optional[str] = Field(None, max_length=15)
    email: str
    user_sex: Optional[str] = Field(None, max_length=1)
    birth: Optional[int] = Field(None, ge=1945, le=2100)
    user_index: int
    created_at: datetime
    last_active: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResponseUser(BaseModel):
    user: UserDb
    detail: str = "User successfully created"
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class NewUserRegistration(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    birth_date: Optional[date] = Field(None, description="Дата рождения пациента")
    sex: Optional[str] = Field(
        None,
        max_length=1,
        description="Пол пациента, может быть 'M'(мужской) или 'F'(женский)",
    )

    @field_validator("sex")
    def user_sex_must_be_m_or_f(cls, v):
        if v not in ["M", "F"]:
            raise ValueError('user_sex must be "M" or "F"')
        return v


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponseModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    session_id: Optional[str] = None
    requires_master_key: bool = False
    message: Optional[str] = None


class EmailSchema(BaseModel):
    email: EmailStr


class VerificationModel(BaseModel):
    email: EmailStr
    verification_code: int


class ChangePasswordModel(BaseModel):
    email: Optional[str]
    password: str = Field(min_length=6, max_length=20)


class ChangeMyPasswordModel(BaseModel):
    old_password: str = Field(min_length=6, max_length=20)
    new_password: str = Field(min_length=6, max_length=20)


class RecoveryCodeModel(BaseModel):
    email: EmailStr
    recovery_code: str


class PasswordStorageSettings(BaseModel):
    local_password_storage: bool
    cloud_password_storage: bool


class MedicalStorageSettings(BaseModel):
    local_medical_storage: bool
    cloud_medical_storage: bool


class UserSessionModel(BaseModel):
    cor_id: Optional[str] = Field(None, max_length=15)
    device_type: str
    device_info: str
    ip_address: str
    device_os: str
    refresh_token: str
    jti: str
    access_token: str


class UserSessionResponseModel(BaseModel):
    id: str
    user_id: str
    device_type: str
    device_info: str
    ip_address: str
    device_os: str
    created_at: datetime
    updated_at: datetime
    jti: Optional[str]
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    region_name: Optional[str] = None
    city_name: Optional[str] = None


class UserSessionDBModel(BaseModel):
    id: str
    cor_id: Optional[str] = Field(None, max_length=15)
    device_type: str
    device_info: str
    ip_address: str
    device_os: str
    refresh_token: str
    created_at: datetime
    updated_at: datetime


# PASS-MANAGER MODELS

class CreateRecordModel(BaseModel):
    record_name: str = Field(max_length=25)
    website: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None



class RecordResponse(BaseModel):
    record_id: int
    record_name: str
    website: str
    username: str
    password: str
    created_at: datetime
    edited_at: datetime
    notes: str
    user_id: str
    is_favorite: bool

    # tags: List[TagModel]

    class Config:
        from_attributes = True


class MainscreenRecordResponse(BaseModel):
    record_id: int
    record_name: str
    website: str
    username: str
    password: str
    is_favorite: bool

    class Config:
        from_attributes = True


class UpdateRecordModel(BaseModel):
    record_name: str = Field(max_length=25)
    website: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None



# PASS-GENERATOR MODELS


class PasswordGeneratorSettings(BaseModel):
    length: int = Field(12, ge=8, le=128)
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_digits: bool = True
    include_special: bool = True


class WordPasswordGeneratorSettings(BaseModel):
    length: int = Field(4, ge=1, le=7)
    separator_hyphen: bool = True
    separator_underscore: bool = True
    include_uppercase: bool = True


# MEDICAL MODELS


class CreateCorIdModel(BaseModel):
    medical_institution_code: str = Field(max_length=3)
    patient_number: str = Field(max_length=3)
    patient_birth: int = Field(ge=1900, le=2100)
    patient_sex: str = Field(max_length=1)

    @field_validator("patient_sex")
    def patient_sex_must_be_m_or_f(cls, v):
        if v not in ["M", "F"]:
            raise ValueError('patient_sex must be "M" or "F"')
        return v


class ResponseCorIdModel(BaseModel):
    cor_id: str = None


# DOCTOR MODELS


class DiplomaCreate(BaseModel):
    scan: Optional[bytes] = Field(None, description="Скан диплома")
    date: Optional[datetime] = Field(..., description="Дата выдачи диплома")
    series: str = Field(..., max_length=50, description="Серия диплома")
    number: str = Field(..., max_length=50, description="Номер диплома")
    university: str = Field(..., max_length=250, description="Название ВУЗа")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DiplomaResponse(BaseModel):
    id: str = Field(..., description="ID диплома")
    date: Optional[datetime] = Field(..., description="Дата выдачи диплома")
    series: str = Field(..., description="Серия диплома")
    number: str = Field(..., description="Номер диплома")
    university: str = Field(..., description="Название ВУЗа")
    file_data: Optional[str] = Field(
        None,
        description="Ссылка на документ",
    )

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class CertificateCreate(BaseModel):
    scan: Optional[bytes] = Field(None, description="Скан сертификата")
    date: Optional[datetime] = Field(..., description="Дата выдачи сертификата")
    series: str = Field(..., max_length=50, description="Серия сертификата")
    number: str = Field(..., max_length=50, description="Номер сертификата")
    university: str = Field(..., max_length=250, description="Название ВУЗа")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class CertificateResponse(BaseModel):
    id: str = Field(..., description="ID сертификата")
    date: Optional[datetime] = Field(..., description="Дата выдачи сертификата")
    series: str = Field(..., description="Серия сертификата")
    number: str = Field(..., description="Номер сертификата")
    university: str = Field(..., description="Название ВУЗа")
    file_data: Optional[str] = Field(
        None,
        description="Ссылка на документ",
    )

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ClinicAffiliationCreate(BaseModel):
    clinic_name: str = Field(..., max_length=250, description="Название клиники")
    department: Optional[str] = Field(None, max_length=250, description="Отделение")
    position: Optional[str] = Field(None, max_length=250, description="Должность")
    specialty: Optional[str] = Field(None, max_length=250, description="Специальность")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ClinicAffiliationResponse(BaseModel):
    id: str = Field(..., description="ID клиники")
    clinic_name: str = Field(..., description="Название клиники")
    department: Optional[str] = Field(None, description="Отделение")
    position: Optional[str] = Field(None, description="Должность")
    specialty: Optional[str] = Field(None, description="Специальность")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class DoctorWithRelationsResponse(BaseModel):
    id: str
    doctor_id: str
    work_email: str
    phone_number: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    doctors_photo: Optional[str] = Field(None, description="Ссылка на фото")
    scientific_degree: Optional[str]
    date_of_last_attestation: Optional[date]
    passport_code: Optional[str] = Field(None, description="Номер паспорта")
    taxpayer_identification_number: Optional[str] = Field(None, description="ИНН")
    place_of_registration: Optional[str] = Field(None, description="Место прописки")
    status: str
    diplomas: List[DiplomaResponse] = []
    certificates: List[CertificateResponse] = []
    clinic_affiliations: List[ClinicAffiliationResponse] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class DoctorCreate(BaseModel):
    work_email: EmailStr = Field(
        ..., description="Рабочий имейл, должен быть уникальным"
    )
    phone_number: Optional[str] = Field(None, description="Номер телефона")
    first_name: str = Field(..., description="Имя врача")
    middle_name: str = Field(..., description="Отчество врача")
    last_name: str = Field(..., description="Фамилия врача")
    passport_code: str = Field(..., description="Номер паспорта")
    taxpayer_identification_number: str = Field(..., description="ИНН")
    place_of_registration: str = Field(..., description="Место прописки")
    scientific_degree: Optional[str] = Field(None, description="Научная степень")
    date_of_last_attestation: Optional[date] = Field(
        None, description="Дата последней атестации"
    )
    diplomas: List[DiplomaCreate] = []
    certificates: List[CertificateCreate] = []
    clinic_affiliations: List[ClinicAffiliationCreate] = []

    class Config:
        json_schema_extra = {
            "example": {
                "work_email": "doctor@example.com",
                "phone_number": "+3806666666",
                "first_name": "John",
                "middle_name": "Doe",
                "last_name": "Smith",
                "passport_code": "CN123456",
                "taxpayer_identification_number": "1234567890",
                "place_of_registration": "Kyiv, Antona Tsedica 12",
                "scientific_degree": "PhD",
                "date_of_last_attestation": "2022-12-31",
                "diplomas": [
                    {
                        "date": "2023-01-01",
                        "series": "AB",
                        "number": "123456",
                        "university": "Medical University",
                    }
                ],
                "certificates": [
                    {
                        "date": "2023-01-01",
                        "series": "CD",
                        "number": "654321",
                        "university": "Another University",
                    }
                ],
                "clinic_affiliations": [
                    {
                        "clinic_name": "City Hospital",
                        "department": "Cardiology",
                        "position": "Senior Doctor",
                        "specialty": "Cardiologist",
                    }
                ],
            }
        }


class DoctorResponse(BaseModel):
    id: str = Field(..., description="ID врача")
    doctor_id: str = Field(..., description="COR-ID врача")
    work_email: EmailStr = Field(..., description="Рабочий имейл")
    phone_number: Optional[str] = Field(None, description="Номер телефона")
    first_name: Optional[str] = Field(None, description="Имя врача")
    middle_name: Optional[str] = Field(None, description="Отчество врача")
    last_name: Optional[str] = Field(None, description="Фамилия врача")
    doctors_photo: Optional[str] = Field(None, description="Ссылка на фото врача")
    scientific_degree: Optional[str] = Field(None, description="Научная степень")
    date_of_last_attestation: Optional[date] = Field(
        None, description="Дата последней атестации"
    )
    status: Doctor_Status
    place_of_registration: Optional[str] = Field(None, description="Место прописки")
    passport_code: Optional[str] = Field(None, description="Номер паспорта")
    taxpayer_identification_number: Optional[str] = Field(None, description="ИНН")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class DoctorResponseForSignature(BaseModel):
    id: str = Field(..., description="ID врача")
    doctor_id: str = Field(..., description="COR-ID врача")
    work_email: EmailStr = Field(..., description="Рабочий имейл")
    phone_number: Optional[str] = Field(None, description="Номер телефона")
    first_name: Optional[str] = Field(None, description="Имя врача")
    middle_name: Optional[str] = Field(None, description="Отчество врача")
    last_name: Optional[str] = Field(None, description="Фамилия врача")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class DoctorCreateResponse(BaseModel):
    id: str = Field(..., description="ID врача")
    doctor_cor_id: str = Field(..., description="COR-ID врача")
    work_email: EmailStr = Field(..., description="Рабочий имейл")
    phone_number: Optional[str] = Field(None, description="Номер телефона")
    first_name: str = Field(..., description="Имя врача")
    middle_name: str = Field(..., description="Отчество врача")
    last_name: str = Field(..., description="Фамилия врача")
    scientific_degree: Optional[str] = Field(None, description="Научная степень")
    date_of_last_attestation: Optional[date] = Field(
        None, description="Дата последней атестации"
    )
    status: Doctor_Status
    place_of_registration: Optional[str] = Field(None, description="Место прописки")
    passport_code: Optional[str] = Field(None, description="Номер паспорта")
    taxpayer_identification_number: Optional[str] = Field(None, description="ИНН")
    diploma_id: List = Field(..., description="ID дипломов")
    certificates_id: List = Field(..., description="ID сертификатов")
    clinic_affiliations_id: List = Field(..., description="ID записей о клиниках")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


# PATIENTS MODELS


class PatientResponce(BaseModel):
    patient_cor_id: str
    encrypted_surname: Optional[bytes] = None
    encrypted_first_name: Optional[bytes] = None
    encrypted_middle_name: Optional[bytes] = None
    sex: Optional[str]
    birth_date: Optional[date]
    status: Optional[str]


class PatientDecryptedResponce(BaseModel):
    patient_cor_id: str
    surname: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    sex: Optional[str]
    birth_date: Optional[Union[date, int]] = None
    age: Optional[int] = None
    status: Optional[PatientStatus] = None


class PaginatedPatientsResponse(BaseModel):
    items: List[PatientResponce]
    total: int


class ExistingPatientRegistration(BaseModel):
    email: Optional[EmailStr] = Field(
        None, description="Email пациента (будет использован для создания пользователя)"
    )
    birth_date: int = Field(..., description="Дата рождения пациента")
    sex: str = Field(
        ...,
        max_length=1,
        description="Пол пациента, может быть 'M'(мужской) или 'F'(женский)",
    )

    @field_validator("sex")
    @classmethod
    def validate_sex_and_normalize(cls, v: str) -> str:
        normalized_v = v.upper()
        if normalized_v not in ["M", "F"]:
            raise ValueError('Пол пациента должен быть "M" или "F".')
        return normalized_v


class NewPatientRegistration(BaseModel):
    email: Optional[EmailStr] = Field(
        None, description="Email пациента (будет использован для создания пользователя)"
    )
    last_name: str = Field(..., min_length=1, description="Фамилия пациента")
    first_name: str = Field(..., min_length=1, description="Имя пациента")
    middle_name: Optional[str] = Field(None, description="Отчество пациента")
    birth_date: date = Field(..., description="Дата рождения пациента")
    sex: str = Field(
        ...,
        max_length=1,
        description="Пол пациента, может быть 'M'(мужской) или 'F'(женский)",
    )
    phone_number: Optional[str] = Field(None, description="Номер телефона пациента")
    address: Optional[str] = Field(None, description="Адрес пациента")

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, v: Optional[str]) -> Optional[str]:
        if v == "":
            return None
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            raise ValueError("Необходимо указать дату рождения")

        min_birth_date = date(1900, 1, 1)
        current_date = date.today()

        if v < min_birth_date:
            raise ValueError("Дата рождения не может быть раньше 1 января 1900 года.")

        if v > current_date:
            raise ValueError("Дата рождения не может быть в будущем.")

        return v

    @field_validator("sex")
    @classmethod
    def validate_sex_and_normalize(cls, v: str) -> str:
        normalized_v = v.upper()
        if normalized_v not in ["M", "F"]:
            raise ValueError('Пол пациента должен быть "M" или "F".')
        return normalized_v


class ExistingPatientAdd(BaseModel):
    cor_id: str = Field(
        ...,
        min_length=10,
        max_length=18,
        description="Cor ID существующего пользователя",
    )


class PatientCreationResponse(BaseModel):
    id: str
    patient_cor_id: str
    user_id: Optional[str] = None
    encrypted_surname: Optional[bytes]
    encrypted_first_name: Optional[bytes]
    encrypted_middle_name: Optional[bytes]
    birth_date: Optional[date]
    sex: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    address: Optional[str]

    class Config:
        from_attributes = True  # Для совместимости с SQLAlchemy


# Модели для лабораторных исследований


class CaseOwnerResponse(BaseModel):
    id: Optional[str] = Field(None, description="ID врача")
    doctor_id: Optional[str] = Field(None, description="COR-ID врача")
    work_email: Optional[EmailStr] = Field(None, description="Рабочий имейл")
    phone_number: Optional[str] = Field(None, description="Номер телефона")
    first_name: Optional[str] = Field(None, description="Имя врача")
    middle_name: Optional[str] = Field(None, description="Отчество врача")
    last_name: Optional[str] = Field(None, description="Фамилия врача")
    is_case_owner: Optional[bool] = Field(False, description="Владелец кейса")


class GlassBase(BaseModel):
    glass_number: int
    staining: Optional[str] = None


class GlassCreate(BaseModel):
    cassette_id: str
    staining_type: StainingType = Field(
        ...,
        description="Тип окрашивания для стекла",
        example=StainingType.HE,
    )
    num_glasses: int = Field(default=1, description="Количество создаваемых стекол")


class ChangeGlassStaining(BaseModel):
    staining_type: StainingType = Field(
        ...,
        description="Тип окрашивания для стекла",
        example=StainingType.HE,
    )


class Glass(GlassBase):
    id: str
    cassette_id: str
    is_printed: Optional[bool]

    class Config:
        from_attributes = True


class GlassForGlassPage(GlassBase):
    id: str
    # cassette_id: str

    class Config:
        from_attributes = True


class DeleteGlassesRequest(BaseModel):
    glass_ids: List[str]


class DeleteGlassesResponse(BaseModel):
    deleted_count: int
    message: str
    not_found_ids: List[str] | None = None


class GetSample(BaseModel):
    sample_id: str


class SampleBase(BaseModel):
    sample_number: str
    archive: bool = False
    cassette_count: int = 0
    glass_count: int = 0


class SampleCreate(BaseModel):
    case_id: str
    num_samples: int = 1


class CassetteBase(BaseModel):
    cassette_number: str
    comment: Optional[str] = None


class CassetteCreate(BaseModel):
    sample_id: str
    num_cassettes: int = 1


class CassetteUpdateComment(BaseModel):
    comment: Optional[str] = None


class Cassette(CassetteBase):
    id: str
    sample_id: str
    glasses: List["Glass"] = []

    class Config:
        from_attributes = True


class Cassette(CassetteBase):
    id: str
    sample_id: str
    is_printed: Optional[bool]
    glasses: List[Glass] = []

    class Config:
        from_attributes = True


class CassetteForGlassPage(BaseModel):
    # id: str
    # sample_id: str
    cassette_number: str
    glasses: List[Glass] = []

    class Config:
        from_attributes = True


class DeleteCassetteRequest(BaseModel):
    cassette_ids: List[str]


class DeleteCassetteResponse(BaseModel):
    deleted_count: int
    message: str


class Sample(SampleBase):
    id: str
    case_id: str
    macro_description: Optional[str] = None
    is_printed_cassette: Optional[bool]
    is_printed_glass: Optional[bool]
    cassettes: List[Cassette] = []

    class Config:
        from_attributes = True


class SampleForGlassPage(BaseModel):
    sample_number: str
    cassettes: List[CassetteForGlassPage] = []

    class Config:
        from_attributes = True


class UpdateSampleMacrodescription(BaseModel):
    macro_description: str


class DeleteSampleRequest(BaseModel):
    sample_ids: List[str]


class DeleteSampleResponse(BaseModel):
    deleted_count: int
    message: str


class DeleteCasesRequest(BaseModel):
    case_ids: List[str]


class DeleteCasesResponse(BaseModel):
    deleted_count: int
    message: str


class CaseBase(BaseModel):
    patient_cor_id: str


class CaseCreate(BaseModel):
    patient_cor_id: str
    num_cases: int = 1
    urgency: UrgencyType = Field(
        ...,
        description="Срочность иссследования",
        example=UrgencyType.S,
    )
    material_type: MaterialType = Field(
        ...,
        description="Тип исследования",
        example=MaterialType.R,
    )
    num_samples: int = Field(
        1, ge=1, description="Количество семплов для создания в каждом кейсе"
    )


class CaseCreateResponse(BaseModel):
    id: str
    case_code: str
    patient_id: str
    grossing_status: str
    creation_date: datetime
    cassette_count: int
    bank_count: int
    glass_count: int


class UpdateCaseCode(BaseModel):
    case_id: str
    update_data: str = Field(
        min_length=5,
        max_length=5,
        description="Последние 5 целочисельных символлов кода кейса",
    )


class Case(BaseModel):
    id: str
    creation_date: datetime
    patient_id: str
    case_code: str
    bank_count: int
    cassette_count: int
    glass_count: int
    pathohistological_conclusion: Optional[str] = None
    microdescription: Optional[str] = None
    grossing_status: Optional[str] = None
    is_printed_cassette: Optional[bool]
    is_printed_glass: Optional[bool]
    is_printed_qr: Optional[bool]

    class Config:
        from_attributes = True


class UpdateCaseCodeResponce(BaseModel):
    id: str
    patient_id: str
    creation_date: datetime
    case_code: str
    bank_count: int
    cassette_count: int
    glass_count: int

    class Config:
        from_attributes = True


class FirstCaseDetailsSchema(BaseModel):
    id: str
    case_code: str
    creation_date: datetime
    is_printed_cassette: Optional[bool]
    is_printed_glass: Optional[bool]
    is_printed_qr: Optional[bool]
    samples: List[Sample]


class PatientFirstCaseDetailsResponse(BaseModel):
    all_cases: List[Case]
    first_case_details: Optional[FirstCaseDetailsSchema] = None


class CaseParametersScheema(BaseModel):
    case_id: str
    macro_archive: MacroArchive
    decalcification: DecalcificationType
    sample_type: SampleType
    material_type: MaterialType
    urgency: UrgencyType
    container_count_actual: Optional[int]
    fixation: FixationType
    macro_description: Optional[str]

    class Config:
        from_attributes = True


class SampleWithoutCassettesSchema(BaseModel):
    id: str
    sample_number: str
    case_id: str
    archive: bool
    cassette_count: int
    glass_count: int
    cassettes: List = []  # Для остальных семплов список кассет будет пустой


class CaseDetailsResponse(BaseModel):
    id: str
    case_code: str
    creation_date: datetime
    bank_count: int
    cassette_count: int
    glass_count: int
    pathohistological_conclusion: Optional[str] = None
    microdescription: Optional[str] = None
    is_printed_cassette: Optional[bool]
    is_printed_glass: Optional[bool]
    is_printed_qr: Optional[bool]
    samples: List[SampleWithoutCassettesSchema | Sample]

    class Config:
        from_attributes = True


class SimpleCaseResponse(BaseModel):
    id: str
    case_code: str
    creation_date: datetime
    bank_count: int
    cassette_count: int
    glass_count: int
    pathohistological_conclusion: Optional[str] = None
    microdescription: Optional[str] = None


class CaseListResponse(BaseModel):
    items: List[Union[CaseDetailsResponse, SimpleCaseResponse]]


class CreateSampleWithDetails(BaseModel):
    created_samples: List[Sample]
    first_sample_details: Optional[Sample] = None


# Модели для принтеров


class CreatePrintingDevice(BaseModel):
    device_class: str = Field(None, description="Клас устройства")
    device_identifier: str = Field(None, description="Идентификатор устройства")
    subnet_mask: Optional[str] = Field(None, max_length=20, description="Маска подсети")
    gateway: Optional[str] = Field(None, max_length=20, description="Шлюз")
    ip_address: str = Field(max_length=20, description="IP-адрес")
    port: Optional[int] = Field(None, le=65535, description="Порт")
    comment: Optional[str] = Field(None, description="Комментарий")
    location: Optional[str] = Field(None, description="Локация")


class ResponcePrintingDevice(BaseModel):
    id: str
    device_class: str
    device_identifier: str
    subnet_mask: Optional[str]
    gateway: Optional[str]
    ip_address: str
    port: Optional[int]
    comment: Optional[str]
    location: Optional[str]


class UpdatePrintingDevice(BaseModel):
    device_class: str = Field(None, description="Клас устройства")
    device_identifier: str = Field(None, description="Идентификатор устройства")
    subnet_mask: Optional[str] = Field(None, max_length=20, description="Маска подсети")
    gateway: Optional[str] = Field(None, max_length=20, description="Шлюз")
    ip_address: str = Field(max_length=20, description="IP-адрес")
    port: Optional[int] = Field(None, le=65535, description="Порт")
    comment: Optional[str] = Field(None, description="Комментарий")
    location: Optional[str] = Field(None, description="Локация")


class Label(BaseModel):
    models_id: int
    content: str
    uuid: Optional[str] = None


class PrintRequest(BaseModel):
    labels: List[Label]


class ReferralAttachmentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    file_url: Optional[str] = Field(None, description="URL файла")

    class Config:
        from_attributes = True


class ReferralAttachmentCreate(BaseModel):
    filename: str
    content_type: str
    file_data: bytes


class ReferralCreate(BaseModel):
    case_id: str = Field(..., description="ID связанного кейса")
    biomaterial_date: Optional[date] = Field(
        None, description="Дата забора биоматериала"
    )
    research_type: Optional[StudyType] = Field(None, description="Вид исследования")
    container_count: Optional[int] = Field(
        None, description="Фактическое количество контейнеров"
    )
    medical_card_number: Optional[str] = Field(None, description="Номер медкарты")
    clinical_data: Optional[str] = Field(None, description="Клинические данные")
    clinical_diagnosis: Optional[str] = Field(None, description="Клинический диагноз")
    medical_institution: Optional[str] = Field(
        None, description="Медицинское учреждение"
    )
    department: Optional[str] = Field(None, description="Отделение")
    attending_doctor: Optional[str] = Field(None, description="Лечащий врач")
    doctor_contacts: Optional[str] = Field(None, description="Контакты врача")
    medical_procedure: Optional[str] = Field(None, description="Медицинская процедура")
    final_report_delivery: Optional[str] = Field(
        None, description="Финальный репорт отправить"
    )
    issued_at: Optional[date] = Field(None, description="Выдано (дата)")


class ReferralResponse(BaseModel):
    id: str
    case_id: str
    case_number: str
    created_at: datetime
    biomaterial_date: Optional[date]
    research_type: Optional[StudyType]
    container_count: Optional[int]
    medical_card_number: Optional[str]
    clinical_data: Optional[str]
    clinical_diagnosis: Optional[str]
    medical_institution: Optional[str]
    department: Optional[str]
    attending_doctor: Optional[str]
    doctor_contacts: Optional[str]
    medical_procedure: Optional[str]
    final_report_delivery: Optional[str]
    issued_at: Optional[date]
    attachments: List[ReferralAttachmentResponse] = []

    class Config:
        from_attributes = True


class ReferralResponseForDoctor(BaseModel):
    case_details: Optional[Case]
    case_owner: Optional[CaseOwnerResponse]
    referral_id: Optional[str] = Field(..., description="Referral ID")
    attachments: Optional[List[ReferralAttachmentResponse]] = []

    class Config:
        from_attributes = True


class ReferralUpdate(BaseModel):
    case_number: Optional[str] = None
    research_type: Optional[str] = None
    container_count: Optional[int] = None
    medical_card_number: Optional[str] = None
    clinical_data: Optional[str] = None
    clinical_diagnosis: Optional[str] = None
    medical_institution: Optional[str] = None
    department: Optional[str] = None
    attending_doctor: Optional[str] = None
    doctor_contacts: Optional[str] = None
    medical_procedure: Optional[str] = None
    final_report_delivery: Optional[str] = None
    issued_at: Optional[date] = None

    class Config:
        from_attributes = True


class ProfileCreate(BaseModel):
    surname: Optional[str] = Field(None, max_length=25, description="Фамилия")
    first_name: Optional[str] = Field(None, max_length=25, description="Имя")
    middle_name: Optional[str] = Field(None, max_length=25, description="Отчество")
    birth_date: Optional[date] = Field(None, description="Дата рождения")
    phone_number: Optional[str] = Field(
        None, max_length=15, description="Номер телефона"
    )
    city: Optional[str] = Field(None, max_length=50, description="Город")
    car_brand: Optional[str] = Field(None, max_length=50, description="Марка авто")
    engine_type: Optional[str] = Field(None, max_length=50, description="Тип двигателя")
    fuel_tank_volume: Optional[int] = Field(
        None, ge=0, le=1000, description="Обьем бензобака"
    )

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    email: str = Field(description="Имейл пользователя")
    sex: str = Field(description="Пол пользователя")
    surname: Optional[str] = Field(None, description="Фамилия")
    first_name: Optional[str] = Field(None, description="Имя")
    middle_name: Optional[str] = Field(None, description="Отчество")
    birth_date: Optional[date] = Field(None, description="Дата рождения")
    phone_number: Optional[str] = Field(None, description="Номер телефона")
    city: Optional[str] = Field(None, description="Город")
    car_brand: Optional[str] = Field(None, description="Марка авто")
    engine_type: Optional[str] = Field(None, description="Тип двигателя")
    fuel_tank_volume: Optional[int] = Field(
        None, ge=0, le=1000, description="Обьем бензобака"
    )

    class Config:
        from_attributes = True


class DeleteMyAccount(BaseModel):
    password: str = Field(min_length=6, max_length=20)


class FullUserInfoResponse(BaseModel):
    user_info: UserDb
    user_roles: Optional[List[str]] = None
    profile: Optional[ProfileResponse] = None
    doctor_info: Optional[DoctorWithRelationsResponse] = None

    class Config:
        from_attributes = True


class UserDataResponse(BaseModel):
    user_info: UserDb

    class Config:
        from_attributes = True


class UserProfileResponseForAdmin(BaseModel):
    profile: Optional[ProfileResponse] = None

    class Config:
        from_attributes = True


class UserDoctorsDataResponseForAdmin(BaseModel):
    doctor_info: Optional[DoctorWithRelationsResponse] = None

    class Config:
        from_attributes = True


class UserRolesResponseForAdmin(BaseModel):
    user_roles: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ReferralFileSchema(BaseModel):
    id: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_url: Optional[str] = None

    class Config:
        from_attributes = True


class FirstCaseReferralDetailsSchema(BaseModel):
    id: str
    case_code: str
    creation_date: datetime
    pathohistological_conclusion: Optional[str] = None
    microdescription: Optional[str] = None
    general_macrodescription: Optional[str] = None
    grossing_status: Optional[str] = None
    patient_cor_id: Optional[str] = None

    attachments: Optional[List[ReferralFileSchema]] = None

    class Config:
        from_attributes = True


class DoctorSignatureBase(BaseModel):
    signature_name: Optional[str] = None
    is_default: bool = False


class DoctorSignatureCreate(DoctorSignatureBase):
    pass


class DoctorSignatureResponse(DoctorSignatureBase):
    id: str
    doctor_id: str
    signature_scan_data: Optional[str] = None
    signature_scan_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportSignatureSchema(BaseModel):
    id: str
    doctor: DoctorResponseForSignature
    signed_at: Optional[datetime] = None

    doctor_signature: Optional[DoctorSignatureResponse] = None

    class Config:
        from_attributes = True


class ReportBaseSchema(BaseModel):
    immunohistochemical_profile: Optional[str] = None
    molecular_genetic_profile: Optional[str] = None
    pathomorphological_diagnosis: Optional[str] = None
    icd_code: Optional[str] = None
    comment: Optional[str] = None

    attached_glass_ids: Optional[List[str]] = None


class ReportCreateSchema(ReportBaseSchema):
    pass


class ReportUpdateSchema(ReportBaseSchema):
    pass


class DoctorDiagnosisSchema(BaseModel):
    id: str
    report_id: str
    doctor: DoctorResponseForSignature
    created_at: datetime
    immunohistochemical_profile: Optional[str] = None
    molecular_genetic_profile: Optional[str] = None
    pathomorphological_diagnosis: Optional[str] = None
    icd_code: Optional[str] = None
    comment: Optional[str] = None
    report_microdescription: Optional[str] = None
    report_macrodescription: Optional[str] = None
    signature: Optional[ReportSignatureSchema] = None

    class Config:
        from_attributes = True


class FinalReportResponseSchema(BaseModel):
    id: Optional[str] = None
    case_id: str
    case_code: str

    biopsy_date: Optional[date] = None
    arrival_date: Optional[date] = None
    report_date: Optional[date] = None

    patient_cor_id: Optional[str] = None
    patient_first_name: Optional[str] = None
    patient_surname: Optional[str] = None
    patient_middle_name: Optional[str] = None
    patient_sex: Optional[str] = None
    patient_birth_date: Optional[date] = None
    patient_full_age: Optional[int] = None
    patient_phone_number: Optional[str] = None
    patient_email: Optional[str] = None

    concatenated_macro_description: Optional[str] = None

    medical_card_number: Optional[str] = None
    medical_institution: Optional[str] = None
    medical_department: Optional[str] = None
    attending_doctor: Optional[str] = None
    clinical_data: Optional[str] = None
    clinical_diagnosis: Optional[str] = None

    painting: Optional[List[StainingType]] = None

    macroarchive: Optional[MacroArchive] = None
    decalcification: Optional[DecalcificationType] = None
    fixation: Optional[FixationType] = None
    num_blocks: Optional[int] = None
    containers_recieved: Optional[int] = None
    containers_actual: Optional[int] = None

    doctor_diagnoses: List[DoctorDiagnosisSchema] = []

    # attached_glass_ids: List[str] = []
    attached_glasses: List[Glass] = []

    class Config:
        from_attributes = True


class PatientFinalReportPageResponse(BaseModel):
    all_cases: Optional[List[Case]] = None
    last_case_details: Optional[Case] = None
    case_owner: Optional[CaseOwnerResponse]
    report_details: Optional[FinalReportResponseSchema]

    class Config:
        from_attributes = True


class CaseFinalReportPageResponse(BaseModel):
    case_details: Case
    case_owner: Optional[CaseOwnerResponse]
    report_details: Optional[FinalReportResponseSchema]

    class Config:
        from_attributes = True


class PatientCasesWithReferralsResponse(BaseModel):
    all_cases: List[Case]
    case_details: Optional[Case]
    case_owner: Optional[CaseOwnerResponse]
    first_case_direction: Optional[FirstCaseReferralDetailsSchema] = None

    class Config:
        from_attributes = True


class FirstCaseGlassDetailsSchema(BaseModel):
    id: str
    case_code: str
    creation_date: datetime
    pathohistological_conclusion: Optional[str] = None
    microdescription: Optional[str] = None
    general_macrodescription: Optional[str] = None
    grossing_status: Optional[str] = None
    patient_cor_id: Optional[str] = None
    is_printed_cassette: Optional[bool]
    is_printed_glass: Optional[bool]
    is_printed_qr: Optional[bool]

    samples: List[SampleForGlassPage]

    class Config:
        from_attributes = True


class PatientGlassPageResponse(BaseModel):
    all_cases: List[Case]
    first_case_details_for_glass: Optional[FirstCaseGlassDetailsSchema] = None
    case_owner: Optional[CaseOwnerResponse]
    report_details: Optional[FinalReportResponseSchema]

    class Config:
        from_attributes = True


class SingleCaseGlassPageResponse(BaseModel):
    single_case_for_glass_page: Optional[FirstCaseGlassDetailsSchema] = None
    case_owner: Optional[CaseOwnerResponse]
    report_details: Optional[FinalReportResponseSchema]


class PathohistologicalConclusionResponse(BaseModel):
    pathohistological_conclusion: Optional[str] = None


class UpdatePathohistologicalConclusion(BaseModel):
    pathohistological_conclusion: str


class MicrodescriptionResponse(BaseModel):
    microdescription: Optional[str] = None


class UpdateMicrodescription(BaseModel):
    microdescription: str


class SampleForExcisionPage(BaseModel):
    id: str
    sample_number: str
    is_archived: bool = False
    macro_description: Optional[str] = None

    class Config:
        from_attributes = True


class LastCaseExcisionDetailsSchema(BaseModel):
    id: str
    case_code: str
    creation_date: datetime
    pathohistological_conclusion: Optional[str] = None
    microdescription: Optional[str] = None
    case_parameters: Optional[CaseParametersScheema] = None
    grossing_status: Optional[str] = None
    patient_cor_id: Optional[str] = None
    is_printed_cassette: Optional[bool]
    is_printed_glass: Optional[bool]
    is_printed_qr: Optional[bool]

    samples: List[SampleForExcisionPage]

    class Config:
        from_attributes = True


class PatientExcisionPageResponse(BaseModel):
    all_cases: List[Case]
    last_case_details_for_excision: Optional[LastCaseExcisionDetailsSchema] = None
    case_owner: Optional[CaseOwnerResponse]

    class Config:
        from_attributes = True


class SingleCaseExcisionPageResponse(BaseModel):

    case_details_for_excision: Optional[LastCaseExcisionDetailsSchema] = None
    case_owner: Optional[CaseOwnerResponse]

    class Config:
        from_attributes = True


# Тестовые схемы под репорт
class GlassTestModelScheema(BaseModel):
    id: str
    glass_number: int
    cassette_id: str
    staining: Optional[str] = None


class CassetteTestForGlassPage(BaseModel):
    id: str
    cassette_number: str
    sample_id: str

    glasses: List[GlassTestModelScheema] = []


class SampleTestForGlassPage(BaseModel):
    id: str
    sample_number: str
    case_id: str
    sample_macro_description: Optional[str] = None

    cassettes: List[CassetteTestForGlassPage] = []


class FirstCaseTestGlassDetailsSchema(BaseModel):
    id: str
    case_code: str
    creation_date: datetime
    grossing_status: Optional[str] = None
    samples: List[SampleTestForGlassPage]

    class Config:
        from_attributes = True


class LabAssistantCreate(BaseModel):
    first_name: Optional[str] = Field(
        None, min_length=1, max_length=20, description="Имя лаборанта"
    )
    middle_name: Optional[str] = Field(
        None, min_length=1, max_length=20, description="Отчество лаборанта"
    )
    last_name: Optional[str] = Field(
        None, min_length=1, max_length=20, description="Фамилия лаборанта"
    )

    class Config:
        from_attributes = True


class LabAssistantResponse(BaseModel):

    id: str
    lab_assistant_cor_id: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        from_attributes = True


class PatientResponseForGetPatients(BaseModel):
    id: str
    patient_cor_id: str
    surname: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    change_date: Optional[datetime] = None
    doctor_status: Optional[PatientStatus] = None
    clinic_status: Optional[PatientClinicStatus] = None


class GetAllPatientsResponce(BaseModel):
    patients: List[PatientResponseForGetPatients]
    total_count: int


class LawyerCreate(BaseModel):
    first_name: str = Field(
        ..., min_length=1, max_length=20, description="Имя менеджера энергии"
    )
    middle_name: str = Field(
        ..., min_length=1, max_length=20, description="Отчество менеджера энергии"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=20, description="Фамилия менеджера энергии"
    )

    class Config:
        from_attributes = True


class LawyerResponse(BaseModel):

    id: str
    lawyer_cor_id: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        from_attributes = True


class ReportResponseSchema(BaseModel):
    id: str
    case_id: str
    case_details: Optional[Case] = None
    macro_description_from_case_params: Optional[str] = None
    microdescription_from_case: Optional[str] = None
    concatenated_macro_description: Optional[str] = None

    doctor_diagnoses: List[DoctorDiagnosisSchema] = []

    attached_glasses: List[Glass] = []

    class Config:
        from_attributes = True


class PatientReportPageResponse(BaseModel):
    all_cases: List[Case]

    last_case_for_report: Optional[Case] = None
    report_details: Optional[ReportResponseSchema] = None

    all_glasses_for_last_case: List[FirstCaseGlassDetailsSchema] = []

    class Config:
        from_attributes = True


class SignReportRequest(BaseModel):
    doctor_signature_id: Optional[str] = None


class PatientTestReportPageResponse(BaseModel):
    all_cases: List[Case]
    last_case_for_report: Optional[Case]
    case_owner: Optional[CaseOwnerResponse]
    report_details: Optional[ReportResponseSchema]
    all_glasses_for_last_case: Optional[FirstCaseTestGlassDetailsSchema] = None

    class Config:
        from_attributes = True


class CaseIDReportPageResponse(BaseModel):
    last_case_for_report: Optional[Case] = None
    case_owner: Optional[CaseOwnerResponse]
    report_details: Optional[ReportResponseSchema] = None
    all_glasses_for_last_case: Optional[FirstCaseTestGlassDetailsSchema] = None

    class Config:
        from_attributes = True


class DoctorDiagnosisInputSchema(BaseModel):
    report_microdescription: Optional[str] = None
    report_macrodescription: Optional[str] = None
    pathomorphological_diagnosis: Optional[str] = None
    icd_code: Optional[str] = None
    comment: Optional[str] = None
    immunohistochemical_profile: Optional[str] = None
    molecular_genetic_profile: Optional[str] = None


class ReportAndDiagnosisUpdateSchema(BaseModel):

    attached_glass_ids: Optional[List[str]] = None
    doctor_diagnosis_data: Optional[DoctorDiagnosisInputSchema] = None


class CaseCloseResponse(BaseModel):
    message: str
    case_id: str
    new_status: str


class CaseOwnershipResponse(BaseModel):
    case_details: Optional[CaseDetailsResponse]
    case_owner: Optional[CaseOwnerResponse]

class SearchResultPatientOverview(PatientFirstCaseDetailsResponse):
    search_type: Literal["patient_overview"] = "patient_overview"

class SearchResultCaseDetails(PatientGlassPageResponse): 
    search_type: Literal["case_details"] = "case_details"

SearchResultUnion = Union[
    SearchResultPatientOverview,
    SearchResultCaseDetails
]

class UnifiedSearchResponse(BaseModel):
    data: SearchResultUnion = Field(discriminator='search_type')


class SearchCaseDetailsSimple(BaseModel):
    search_type: Literal["case_details"] = "case_details"
    case_id: str
    patient_id: str

class GeneralPrinting(BaseModel):
    printer_ip: str
    model_id: int
    clinic_name: str
    hooper: str


class GlassPrinting(BaseModel):
    printer_ip: str
    model_id: int
    clinic_name: str
    hooper: str
    glass_id: str
    printing: bool

class GlassResponseForPrinting(BaseModel):

    case_code: str
    sample_number: str
    cassette_number: str
    glass_number: int
    staining: str
    patient_cor_id: str

class CassettePrinting(BaseModel):
    printer_ip: str
    model_id: int
    clinic_name: str
    hooper: str
    cassete_id: str
    printing: bool

class CassetteResponseForPrinting(BaseModel):

    case_code: str
    sample_number: str
    cassette_number: str
    patient_cor_id: str



class PrintLabel(BaseModel):
    """Модель для одной метки для печати."""
    model_id: int
    content: str
    uuid: str 

class PrintRequest(BaseModel):
    """Модель для запроса на печать."""
    printer_ip: str
    labels: List[PrintLabel]