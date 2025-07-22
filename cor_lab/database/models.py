import enum
import uuid
from sqlalchemy import (
    ARRAY,
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    Text,
    Date,
    Index,
    UniqueConstraint,
    func,
    Boolean,
    LargeBinary,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql.sqltypes import DateTime

Base = declarative_base()


class Doctor_Status(enum.Enum):
    pending: str = "pending"
    approved: str = "approved"
    agreed: str = "agreed"
    rejected: str = "rejected"
    need_revision: str = "need_revision"


class PatientStatus(enum.Enum):
    registered = "registered"
    diagnosed = "diagnosed"
    under_treatment = "under_treatment"
    hospitalized = "hospitalized"
    discharged = "discharged"
    died = "died"
    in_process = "in_process"
    referred_for_additional_consultation = "referred_for_additional_consultation"


class PatientClinicStatus(enum.Enum):
    registered = "registered"
    diagnosed = "diagnosed"
    under_treatment = "under_treatment"
    hospitalized = "hospitalized"
    discharged = "discharged"
    died = "died"
    in_process = "in_process"
    referred_for_additional_consultation = "referred_for_additional_consultation"
    awaiting_report = "awaiting_report"
    completed = "completed"
    error = "error"


# Типы макроархива для параметров кейса
class MacroArchive(enum.Enum):
    ESS = "ESS - без остатка"
    RSS = "RSS - остаток"


# Типы декальцинации для параметров кейса
class DecalcificationType(enum.Enum):
    ABSENT = "Отсутствует"
    EDTA = "EDTA"
    ACIDIC = "Кислотная"


# Типы образцов для параметров кейса
class SampleType(enum.Enum):
    NATIVE = "Нативный биоматериал"
    BLOCKS = "Блоки/Стекла"


# Типы материалов (исследований) для параметров кейса
class MaterialType(enum.Enum):
    R = "Resectio"
    B = "Biopsy"
    E = "Excisio"
    C = "Cytology"
    CB = "Cellblock"
    S = "Second Opinion"
    A = "Autopsy"
    EM = "Electron Microscopy"
    OTHER = "Другое"


# Типы срочности для параметров кейса
class UrgencyType(enum.Enum):
    S = "Standard"
    U = "Urgent"
    F = "Frozen"


# Типы фиксации для параметров кейса
class FixationType(enum.Enum):
    NBF_10 = "10% NBF"
    OSMIUM = "Osmium"
    BOUIN = "Bouin"
    ALCOHOL = "Alcohol"
    GLUTARALDEHYDE_2 = "2% Glutaraldehyde"
    OTHER = "Другое"


# Типы исследований для направления
class StudyType(enum.Enum):
    CYTOLOGY = "цитология"
    HISTOPATHOLOGY = "патогистология"
    IMMUNOHISTOCHEMISTRY = "иммуногистохимия"
    FISH_CISH = "FISH/CISH"
    CB = "Cellblock"
    S = "Second Opinion"
    A = "Autopsy"
    EM = "Electron Microscopy"


# Типы окрашивания для стёкол
class StainingType(enum.Enum):
    HE = "H&E"
    ALCIAN_PAS = "Alcian PAS"
    CONGO_RED = "Congo red"
    MASSON_TRICHROME = "Masson Trichrome"
    VAN_GIESON = "van Gieson"
    ZIEHL_NEELSEN = "Ziehl Neelsen"
    WARTHIN_STARRY_SILVER = "Warthin-Starry Silver"
    GROCOTT_METHENAMINE_SILVER = "Grocott's Methenamine Silver"
    TOLUIDINE_BLUE = "Toluidine Blue"
    PERLS_PRUSSIAN_BLUE = "Perls Prussian Blue"
    PAMS = "PAMS"
    PICROSIRIUS = "Picrosirius"
    SIRIUS_RED = "Sirius red"
    THIOFLAVIN_T = "Thioflavin T"
    TRICHROME_AFOG = "Trichrome AFOG"
    VON_KOSSA = "von Kossa"
    GIEMSA = "Giemsa"
    OTHAR = "Othar"


class Grossing_status(enum.Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CREATED = "CREATED"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cor_id = Column(String(250), unique=True, nullable=True)
    email = Column(String(250), unique=True, nullable=False)
    password = Column(String(250), nullable=False)
    user_sex = Column(String(10), nullable=True)
    birth = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    unique_cipher_key = Column(
        String(250), nullable=False
    )
    # Связи

    user_records = relationship(
        "Record", back_populates="user", cascade="all, delete-orphan"
    )
    user_doctors = relationship(
        "Doctor", back_populates="user", cascade="all, delete-orphan"
    )

    patient = relationship("Patient", back_populates="user", uselist=False)
    user_sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    user_lab_assistants = relationship(
        "LabAssistant", back_populates="user", cascade="all, delete-orphan"
    )
    user_lawyers = relationship(
        "Lawyer", back_populates="user", cascade="all, delete-orphan"
    )


    # Индексы
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_cor_id", "cor_id"),
    )

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.cor_id"), nullable=False)
    device_type = Column(String(250), nullable=True)
    device_info = Column(String(250), nullable=True)
    ip_address = Column(String(250), nullable=True)
    device_os = Column(String(250), nullable=True)
    jti = Column(
        String,
        unique=True,
        nullable=True,
        comment="JTI последнего Access токена, выданного для этой сессии",
    )
    refresh_token = Column(LargeBinary, nullable=True)
    access_token = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Связи
    user = relationship("User", back_populates="user_sessions")

    # Индексы
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        UniqueConstraint("user_id", "device_info", name="uq_user_device_session"),
    )

class Record(Base):
    __tablename__ = "records"

    record_id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    record_name = Column(String(250), nullable=False)
    website = Column(String(250), nullable=True)
    username = Column(LargeBinary, nullable=True)
    password = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    edited_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    notes = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False, nullable=True)

    # Связи
    user = relationship("User", back_populates="user_records")

    # Индексы
    __table_args__ = (Index("idx_records_user_id", "user_id"),)

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(
        String(36), ForeignKey("users.cor_id"), unique=True, nullable=False
    )
    phone_number = Column(String(20), nullable=True)
    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    doctors_photo = Column(LargeBinary, nullable=True)
    scientific_degree = Column(String(100), nullable=True)
    date_of_last_attestation = Column(Date, nullable=True)
    status = Column(Enum(Doctor_Status), default=Doctor_Status.pending, nullable=False)
    passport_code = Column(String(20), nullable=True)
    taxpayer_identification_number = Column(String(20), nullable=True)
    reserv_scan_data = Column(LargeBinary, nullable=True)
    reserv_scan_file_type = Column(String, nullable=True)
    date_of_next_review = Column(Date, nullable=True)
    place_of_registration = Column(String, nullable=True)

    user = relationship("User", back_populates="user_doctors")
    diplomas = relationship(
        "Diploma", back_populates="doctor", cascade="all, delete-orphan"
    )
    certificates = relationship(
        "Certificate", back_populates="doctor", cascade="all, delete-orphan"
    )
    clinic_affiliations = relationship(
        "ClinicAffiliation", back_populates="doctor", cascade="all, delete-orphan"
    )
    patient_statuses = relationship(
        "DoctorPatientStatus", back_populates="doctor", cascade="all, delete-orphan"
    )
    signatures = relationship(
        "DoctorSignature", back_populates="doctor", cascade="all, delete-orphan"
    )
    doctor_diagnoses = relationship("DoctorDiagnosis", back_populates="doctor")
    signed_diagnoses = relationship("ReportSignature", back_populates="doctor")
    owned_cases = relationship("Case", back_populates="owner_obj")


class LabAssistant(Base):
    __tablename__ = "lab_assistants"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lab_assistant_cor_id = Column(
        String(36), ForeignKey("users.cor_id"), unique=True, nullable=False
    )
    first_name = Column(String(100), nullable=True)
    surname = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    lab_assistants_photo = Column(LargeBinary, nullable=True)

    user = relationship("User", back_populates="user_lab_assistants")



class Lawyer(Base):
    __tablename__ = "lawyers"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lawyer_cor_id = Column(
        String(36), ForeignKey("users.cor_id"), unique=True, nullable=False
    )
    first_name = Column(String(100), nullable=True)
    surname = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)

    user = relationship("User", back_populates="user_lawyers")


class Diploma(Base):
    __tablename__ = "diplomas"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.doctor_id"), nullable=False)
    file_data = Column(LargeBinary, nullable=True)
    file_type = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    series = Column(String(50), nullable=False)
    number = Column(String(50), nullable=False)
    university = Column(String(250), nullable=False)

    doctor = relationship("Doctor", back_populates="diplomas")


class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.doctor_id"), nullable=False)
    file_data = Column(LargeBinary, nullable=True)
    file_type = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    series = Column(String(50), nullable=False)
    number = Column(String(50), nullable=False)
    university = Column(String(250), nullable=False)

    doctor = relationship("Doctor", back_populates="certificates")


class ClinicAffiliation(Base):
    __tablename__ = "clinic_affiliations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.doctor_id"), nullable=False)
    clinic_name = Column(String(250), nullable=False)
    department = Column(String(250), nullable=True)
    position = Column(String(250), nullable=True)
    specialty = Column(String(250), nullable=True)

    doctor = relationship("Doctor", back_populates="clinic_affiliations")


class Verification(Base):
    __tablename__ = "verification"
    id = Column(Integer, primary_key=True)
    email = Column(String(250), unique=True, nullable=False)
    verification_code = Column(Integer, default=None)
    email_confirmation = Column(Boolean, default=False)

    # Индексы
    __table_args__ = (Index("idx_verification_email", "email"),)



class Patient(Base):
    __tablename__ = "patients"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    patient_cor_id = Column(
        String(250), unique=True, nullable=False
    )  
    user_id = Column(
        String(36), ForeignKey("users.id"), unique=True, nullable=True
    )  

    last_name = Column(String(250), nullable=True) 
    first_name = Column(String(250), nullable=True) 
    middle_name = Column(
        String(250), nullable=True
    )
    birth_date = Column(Date, nullable=True)
    sex = Column(String(10), nullable=True)
    email = Column(String(250), nullable=True)
    phone_number = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    photo = Column(LargeBinary, nullable=True)  # Хранение фото как бинарные данные
    change_date = Column(DateTime, default=func.now(), onupdate=func.now())
    create_date = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="patient")
    doctor_statuses = relationship("DoctorPatientStatus", back_populates="patient")
    clinic_statuses = relationship("PatientClinicStatusModel", back_populates="patient")

    search_tokens = Column(Text, default="", nullable=False)

    def __repr__(self):
        return f"<Patient(id='{self.id}', patient_cor_id='{self.patient_cor_id}')>"


class PatientClinicStatusModel(Base):
    __tablename__ = "clinic_patient_statuses"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    patient_status_for_clinic = Column(
        Enum(PatientClinicStatus), default=PatientClinicStatus.registered
    )
    assigned_date = Column(DateTime, default=func.now())
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now())

    patient = relationship("Patient", back_populates="clinic_statuses")


class DoctorPatientStatus(Base):
    __tablename__ = "doctor_patient_statuses"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    status = Column(Enum(PatientStatus), nullable=False)
    assigned_date = Column(DateTime, default=func.now())
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now())

    patient = relationship("Patient", back_populates="doctor_statuses")
    doctor = relationship("Doctor", back_populates="patient_statuses")

    __table_args__ = (
        # Каждый врач имеет только 1 конкретный статус под пациента
        UniqueConstraint(
            "patient_id", "doctor_id", name="unique_patient_doctor_status"
        ),
    )


# Кейс
class Case(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), index=True)
    creation_date = Column(DateTime, default=func.now())
    case_code = Column(String(250), index=True, unique=True)
    bank_count = Column(Integer, default=0)
    cassette_count = Column(Integer, default=0)
    glass_count = Column(Integer, default=0)
    grossing_status = Column(Enum(Grossing_status), default=Grossing_status.CREATED)
    pathohistological_conclusion = Column(Text, nullable=True)
    microdescription = Column(Text, nullable=True)
    general_macrodescription = Column(Text, nullable=True)
    case_owner = Column(String(36), ForeignKey("doctors.doctor_id"), nullable=True)
    closing_date = Column(DateTime, nullable=True)
    is_printed_cassette = Column(Boolean, nullable=True, default=False)
    is_printed_glass = Column(Boolean, nullable=True, default=False)
    is_printed_qr = Column(Boolean, nullable=True, default=False)

    samples = relationship(
        "Sample", back_populates="case", cascade="all, delete-orphan"
    )
    referral = relationship(
        "Referral", back_populates="case", cascade="all, delete-orphan"
    )
    case_parameters = relationship(
        "CaseParameters",
        uselist=False,
        back_populates="case",
        cascade="all, delete-orphan",
    )
    report = relationship(
        "Report", back_populates="case", uselist=False, cascade="all, delete-orphan"
    )
    owner_obj = relationship(
        "Doctor", back_populates="owned_cases", foreign_keys=[case_owner]
    )


# Банка
class Sample(Base):
    __tablename__ = "samples"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    sample_number = Column(String(50))
    cassette_count = Column(Integer, default=0)
    glass_count = Column(Integer, default=0)
    archive = Column(Boolean, default=False)
    macro_description = Column(Text, nullable=True)
    is_printed_cassette = Column(Boolean, nullable=True, default=False)
    is_printed_glass = Column(Boolean, nullable=True, default=False)

    case = relationship("Case", back_populates="samples")
    cassette = relationship(
        "Cassette", back_populates="sample", cascade="all, delete-orphan"
    )


# Касета
class Cassette(Base):
    __tablename__ = "cassettes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sample_id = Column(String(36), ForeignKey("samples.id"), nullable=False)
    cassette_number = Column(
        String(50)
    )  # Порядковый номер кассеты в рамках конкретной банки
    comment = Column(String(500), nullable=True)
    glass_count = Column(Integer, default=0)
    is_printed = Column(Boolean, nullable=True, default=False)
    glass = relationship(
        "Glass", back_populates="cassette", cascade="all, delete-orphan"
    )
    sample = relationship("Sample", back_populates="cassette")


# Стекло
class Glass(Base):
    __tablename__ = "glasses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cassette_id = Column(String(36), ForeignKey("cassettes.id"), nullable=False)
    glass_number = Column(Integer)  # Порядковый номер стекла
    staining = Column(Enum(StainingType), nullable=True)
    glass_data = Column(LargeBinary, nullable=True)
    is_printed = Column(Boolean, nullable=True, default=False)
    cassette = relationship("Cassette", back_populates="glass")


# Параметры кейса
class CaseParameters(Base):
    __tablename__ = "case_parameters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id"), unique=True, nullable=False)
    macro_archive = Column(Enum(MacroArchive), default=MacroArchive.ESS)
    decalcification = Column(
        Enum(DecalcificationType), default=DecalcificationType.ABSENT
    )
    sample_type = Column(Enum(SampleType), default=SampleType.NATIVE)
    material_type = Column(Enum(MaterialType), default=MaterialType.B)
    urgency = Column(Enum(UrgencyType), default=UrgencyType.S)
    container_count_actual = Column(Integer, nullable=True)
    fixation = Column(Enum(FixationType), default=FixationType.NBF_10)
    macro_description = Column(Text, nullable=True)

    case = relationship("Case", back_populates="case_parameters")


# Направление на исследование
class Referral(Base):
    __tablename__ = "referrals"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    case_id = Column(
        String,
        ForeignKey("cases.id"),
        unique=True,
        nullable=False,
        comment="ID связанного кейса",
    )
    case_number = Column(String, index=True, nullable=False, comment="Номер кейса")
    created_at = Column(
        DateTime, default=func.now(), comment="Дата создания направления"
    )
    research_type = Column(Enum(StudyType), nullable=True, comment="Вид исследования")
    container_count = Column(
        Integer, nullable=True, comment="Фактическое количество контейнеров"
    )
    medical_card_number = Column(String, nullable=True, comment="Номер медкарты")
    clinical_data = Column(Text, nullable=True, comment="Клинические данные")
    clinical_diagnosis = Column(String, nullable=True, comment="Клинический диагноз")
    medical_institution = Column(
        String, nullable=True, comment="Медицинское учреждение"
    )
    department = Column(String, nullable=True, comment="Отделение")
    attending_doctor = Column(String, nullable=True, comment="Лечащий врач")
    doctor_contacts = Column(String, nullable=True, comment="Контакты врача")
    medical_procedure = Column(String, nullable=True, comment="Медицинская процедура")
    final_report_delivery = Column(
        Text, nullable=True, comment="Финальный репорт отправить"
    )
    issued_at = Column(DateTime, nullable=True, comment="Выдано (дата)")
    biomaterial_date = Column(
        DateTime, nullable=True, comment="Дата забора биоматериала"
    )

    case = relationship("Case", back_populates="referral")

    attachments = relationship(
        "ReferralAttachment",
        back_populates="referral",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class ReferralAttachment(Base):
    __tablename__ = "referral_attachments"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    referral_id = Column(
        String,
        ForeignKey("referrals.id"),
        nullable=False,
        comment="ID связанного направления",
    )
    filename = Column(String, nullable=False, comment="Имя файла")
    content_type = Column(
        String,
        nullable=False,
        comment="Тип содержимого (например, image/jpeg, application/pdf)",
    )
    file_data = Column(LargeBinary, nullable=False, comment="Бинарные данные файла")

    referral = relationship("Referral", back_populates="attachments")


class PrintingDevice(Base):
    __tablename__ = "printing_device"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    device_class = Column(String, nullable=False)
    device_identifier = Column(String, nullable=False, unique=True)
    subnet_mask = Column(String, nullable=True)
    gateway = Column(String, nullable=True)
    ip_address = Column(String, nullable=False)
    port = Column(Integer, nullable=True)
    comment = Column(String, nullable=True)
    location = Column(String, nullable=True)


class DoctorSignature(Base):
    __tablename__ = "doctor_signatures"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    signature_name = Column(String(255), nullable=True)
    signature_scan_data = Column(LargeBinary, nullable=True)
    signature_scan_type = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Связи
    doctor = relationship("Doctor", back_populates="signatures")


class ReportSignature(Base):
    __tablename__ = "report_signatures"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    diagnosis_entry_id = Column(
        String(36), ForeignKey("doctor_diagnoses.id"), nullable=True, unique=True
    )
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    doctor_signature_id = Column(
        String(36), ForeignKey("doctor_signatures.id"), nullable=True
    )
    signed_at = Column(DateTime, default=func.now())

    # Связи
    doctor_diagnosis_entry = relationship("DoctorDiagnosis", back_populates="signature")
    doctor = relationship("Doctor")
    doctor_signature = relationship("DoctorSignature")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id"), unique=True, nullable=False)
    attached_glass_ids = Column(ARRAY(String(36)), nullable=True, default=[])
    # Связи
    case = relationship("Case", back_populates="report")
    doctor_diagnoses = relationship(
        "DoctorDiagnosis",
        back_populates="report",
        order_by="DoctorDiagnosis.created_at",
    )


class DoctorDiagnosis(Base):
    __tablename__ = "doctor_diagnoses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.doctor_id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    immunohistochemical_profile = Column(Text, nullable=True)
    molecular_genetic_profile = Column(Text, nullable=True)
    pathomorphological_diagnosis = Column(Text, nullable=True)

    icd_code = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)

    report_macrodescription = Column(Text, nullable=True)
    report_microdescription = Column(Text, nullable=True)

    # Связи
    report = relationship("Report", back_populates="doctor_diagnoses")
    doctor = relationship("Doctor")
    signature = relationship(
        "ReportSignature", uselist=False, back_populates="doctor_diagnosis_entry"
    )

# Base.metadata.create_all(bind=engine)
