from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator
from uuid import UUID
from datetime import date, datetime
from typing import Literal, Any
from app.database.models import PersonContact
from app.schemas.local.local_schemas import LocalResponse
from app.schemas.company import CompanyResponse, CompanyOut
from app.schemas.org_unit_schemas import OrgUnitOut

class UserEmailCreate(BaseModel):
    email: EmailStr
    is_primary: bool = False

class UserContactCreate(BaseModel):
    contact_type: str
    value: str
    description: str | None = None
    is_public: bool = False

class PersonEmailCreate(BaseModel):
    email: EmailStr
    is_primary: bool = False
    scope: str = "personal"
    
    model_config = ConfigDict(from_attributes=True)

class PersonEmailInput(PersonEmailCreate):
    id: int | None = None
    is_verified: bool = False
    verified_at: datetime | None = None

class UserCompanyCreate(BaseModel):
    company_id: int
    is_main: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class UserCompanyInput(BaseModel):
    company_id: int
    is_primary: bool = False
    job_title: str | None = None
    employee_number: str | None = None
    admission_date: date | None = None
    termination_date: date | None = None
    employment_type: str | None = None
    status: str | None = None
    local_id: int | None = None
    org_unit_id: int | None = None

class UserCompanyUpdateInput(BaseModel):
    is_primary: bool | None = None
    job_title: str | None = None
    employee_number: str | None = None
    admission_date: date | None = None
    termination_date: date | None = None
    employment_type: str | None = None
    status: str | None = None
    local_id: int | None = None
    org_unit_id: int | None = None

class PersonContactInput(BaseModel):
    value: str
    contact_type: Literal["TELEMOVEL", "TELEFONE", "DDI"]
    is_public: bool = False
    is_primary: bool = False
    description: str | None = None

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    full_name: str | None = None
    tax_id: str | None = None
    birth_date: date | None = None
    preferred_name: str | None = None
    locale: str = "pt-PT"
    time_zone: str = "Europe/Lisbon"
    company_id: int
    local_id: int | None = None
    org_unit_id: int | None = None
    username: str | None = None
    password: str | None = None
    emails: list[PersonEmailCreate] = []
    contacts: list[PersonContactInput] = []
    companies: list[int] = []
    extra_info: str | None = None

class UserEmailInput(BaseModel):
    email: EmailStr
    is_primary: bool = False
    
class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    tax_id: str | None = None
    birth_date: date | None = None
    preferred_name: str | None = None
    locale: str | None = None
    time_zone: str | None = None
    username: str | None = None
    password: str | None = None
    extra_info: str | None = None
    company_id: int | None = None
    companies: list[int] | None = None
    local_id: int | None = None
    org_unit_id: int | None = None
    emails: list[PersonEmailInput] | None = None
    contacts: list[PersonContactInput] | None = None

class PersonEmailResponse(BaseModel):
    id: int
    email: str
    is_primary: bool
    is_verified: bool
    verified_at: datetime | None = None
    scope: str
    
    model_config = ConfigDict(from_attributes=True)

class PersonContactResponse(BaseModel):
    contact_type: str
    value: str
    description: str | None
    is_public: bool
    is_primary: bool

    @field_validator("contact_type", mode="before")
    @classmethod
    def serialize_contact_type(cls, v):
        if hasattr(v, "slug"):
            return v.slug
        return v

    class Config:
        from_attributes = True

class UserCompanyResponse(BaseModel):
    is_primary: bool
    job_title: str | None = None
    employee_number: str | None = None
    admission_date: date | None = None
    termination_date: date | None = None
    employment_type: str | None = None
    status: str | None = None
    company: CompanyResponse
    local: LocalResponse | None = None
    org_unit: OrgUnitOut | None = None
    
    model_config = ConfigDict(from_attributes=True)

class UserCompanyOut(BaseModel):
    is_primary: bool
    job_title: str | None = None
    employee_number: str | None = None
    admission_date: date | None = None
    termination_date: date | None = None
    employment_type: str | None = None
    status: str | None = None
    company: CompanyOut
    local: LocalResponse | None = None
    org_unit: OrgUnitOut | None = None
    
    model_config = ConfigDict(from_attributes=True)

def inject_profile_data(data: Any) -> Any:
    # Helper for model_validators
    if hasattr(data, 'profile') and data.profile:
        data.first_name = data.profile.first_name
        data.last_name = data.profile.last_name
        data.full_name = data.profile.full_name
        data.tax_id = data.profile.tax_id
        data.birth_date = data.profile.birth_date
        data.preferred_name = data.profile.preferred_name
        data.locale = data.profile.locale
        data.time_zone = data.profile.time_zone
        data.photo_uri = getattr(data.profile, 'photo_uri', None)
        
    if hasattr(data, 'companies') and data.companies:
        primary = next((c for c in data.companies if c.is_primary), None)
        if not primary and len(data.companies) > 0:
            primary = data.companies[0]
        if primary:
            data.job_title = getattr(primary, 'job_title', None)
            data.employee_number = getattr(primary, 'employee_number', None)
            data.local = getattr(primary, 'local', None)
            data.org_unit = getattr(primary, 'org_unit', None)

    if isinstance(data, dict):
        if 'profile' in data and data['profile']:
            prof = data['profile']
            if isinstance(prof, dict):
                data['first_name'] = prof.get('first_name')
                data['last_name'] = prof.get('last_name')
                data['full_name'] = prof.get('full_name')
                data['tax_id'] = prof.get('tax_id')
                data['birth_date'] = prof.get('birth_date')
                data['preferred_name'] = prof.get('preferred_name')
                data['locale'] = prof.get('locale')
                data['time_zone'] = prof.get('time_zone')
                data['photo_uri'] = prof.get('photo_uri')
            else:
                data['first_name'] = getattr(prof, 'first_name', None)
                data['last_name'] = getattr(prof, 'last_name', None)
                data['full_name'] = getattr(prof, 'full_name', None)
                data['tax_id'] = getattr(prof, 'tax_id', None)
                data['birth_date'] = getattr(prof, 'birth_date', None)
                data['preferred_name'] = getattr(prof, 'preferred_name', None)
                data['locale'] = getattr(prof, 'locale', None)
                data['time_zone'] = getattr(prof, 'time_zone', None)
                data['photo_uri'] = getattr(prof, 'photo_uri', None)
            
        if 'companies' in data and data['companies']:
            primary = next((c for c in data['companies'] if (c.get('is_primary') if isinstance(c, dict) else getattr(c, 'is_primary', False))), None)
            if not primary and len(data['companies']) > 0:
                primary = data['companies'][0]
            if primary:
                if isinstance(primary, dict):
                    data['job_title'] = primary.get('job_title')
                    data['employee_number'] = primary.get('employee_number')
                    data['local'] = primary.get('local')
                    data['org_unit'] = primary.get('org_unit')
                else:
                    data['job_title'] = getattr(primary, 'job_title', None)
                    data['employee_number'] = getattr(primary, 'employee_number', None)
                    data['local'] = getattr(primary, 'local', None)
                    data['org_unit'] = getattr(primary, 'org_unit', None)
    return data

class UserDetailsOut(BaseModel):
    id: int
    uuid: UUID
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    tax_id: str | None = None
    birth_date: date | None = None
    preferred_name: str | None = None
    locale: str | None = None
    time_zone: str | None = None
    photo_uri: str | None = None
    employee_number: str | None = None
    username: str | None = None
    job_title: str | None = None
    
    emails: list[PersonEmailResponse] = []
    contacts: list[PersonContactResponse] = []
    
    companies: list[UserCompanyOut] | None = []
    
    extra_info: str | None = None
    local: LocalResponse | None = None
    org_unit: OrgUnitOut | None = None
    permissions: dict[str, list[str]] = {}
    
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def load_profile(cls, data: Any) -> Any:
        return inject_profile_data(data)

class UserResponse(BaseModel):
    id: int
    uuid: UUID
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    tax_id: str | None = None
    birth_date: date | None = None
    preferred_name: str | None = None
    locale: str | None = None
    time_zone: str | None = None
    photo_uri: str | None = None
    employee_number: str | None = None
    username: str | None = None
    job_title: str | None = None
    
    emails: list[PersonEmailResponse] = []
    contacts: list[PersonContactResponse] = []
    
    companies: list[UserCompanyResponse] | None = []
    
    extra_info: str | None = None
    local: LocalResponse | None = None
    org_unit: OrgUnitOut | None = None
    permissions: dict[str, list[str]] = {}
    
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def load_profile(cls, data: Any) -> Any:
        return inject_profile_data(data)

class UserFilter(BaseModel):
    search: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    employee_number: str | None = None
    company_id: int | None = None
    company_name: str | None = None
    local_id: int | None = None
    local_name: str | None = None
    org_unit_id: int | None = None
    email: str | None = None
    contact: str | None = None

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int
    next_page: int | None
    previous_page: int | None

class ContactResponse(BaseModel):
    id: int
    type: str
    value: str

class UserBatchDetail(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    contacts: list[ContactResponse] = []

    @model_validator(mode="before")
    @classmethod
    def load_profile(cls, data: Any) -> Any:
        return inject_profile_data(data)

BatchUserResponse = dict[int, UserBatchDetail]

class UserBatchDetailsOut(BaseModel):
    id: int
    uuid: UUID
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    tax_id: str | None = None
    emails: list[PersonEmailResponse] | None = []
    employee_number: str | None = None
    local: LocalResponse | None = None
    company: CompanyResponse | None = None
    org_unit: OrgUnitOut | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def load_profile(cls, data: Any) -> Any:
        return inject_profile_data(data)
