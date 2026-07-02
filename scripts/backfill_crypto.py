import asyncio
import logging
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from tortoise import Tortoise
from app.core.config import TORTOISE_ORM_CONFIG
from app.database.models import PersonProfile, UserIdentity, PersonEmail, PersonContact, UserCompany
from app.crypto.key_provider import KeyProvider
from app.crypto.crypto_service import CryptoService
from app.crypto.blind_indexer import BlindIndexer
from app.crypto.normalizers import normalize_email, normalize_phone, normalize_text, normalize_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def run_backfill(batch_size=500, delay=0.1):
    logger.info("Starting backfill process...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    logger.info("Database initialized.")

    kp = KeyProvider()
    crypto = CryptoService(kp)
    indexer = BlindIndexer(kp)
    
    current_version = int(kp.current_version.upper().replace("V", ""))
    
    await backfill_person_profile(current_version, crypto, indexer, batch_size, delay)
    await backfill_user_identity(current_version, crypto, indexer, batch_size, delay)
    await backfill_person_email(current_version, crypto, indexer, batch_size, delay)
    await backfill_person_contact(current_version, crypto, indexer, batch_size, delay)
    await backfill_user_company(current_version, crypto, indexer, batch_size, delay)

    logger.info("Backfill process completed.")
    await Tortoise.close_connections()

async def backfill_person_profile(kv: int, crypto: CryptoService, indexer: BlindIndexer, batch_size: int, delay: float):
    logger.info("--- Backfilling PersonProfile ---")
    records = await PersonProfile.all()
    
    migrated = 0
    for r in records:
        needs_update = False
        
        if r.tax_id and not r.tax_id_enc:
            norm_tax = normalize_text(r.tax_id)
            if norm_tax:
                r.tax_id_enc = crypto.encrypt(norm_tax, "person_profile.tax_id")
                r.tax_id_idx = indexer.compute("person_profile.tax_id", norm_tax)
                needs_update = True
                
        if r.tax_id_key_version != kv:
            r.tax_id_key_version = kv
            needs_update = True

        if r.birth_date and not r.birth_date_enc:
            b_val = r.birth_date.isoformat() if hasattr(r.birth_date, 'isoformat') else str(r.birth_date)
            norm_birth = normalize_date(b_val)
            if norm_birth:
                r.birth_date_enc = crypto.encrypt(norm_birth, "person_profile.birth_date")
                needs_update = True
                
        if r.birth_date_key_version != kv:
            r.birth_date_key_version = kv
            needs_update = True
        
        if needs_update:
            await r.save(update_fields=["tax_id_enc", "tax_id_idx", "tax_id_key_version", "birth_date_enc", "birth_date_key_version"])
            migrated += 1
        
    logger.info(f"Scanned batch of {len(records)} PersonProfiles. Updated: {migrated}")

async def backfill_user_identity(kv: int, crypto: CryptoService, indexer: BlindIndexer, batch_size: int, delay: float):
    logger.info("--- Backfilling UserIdentity ---")
    records = await UserIdentity.all()
    
    migrated = 0
    for r in records:
        needs_update = False
        
        if r.identifier and not r.identifier_enc:
            norm = normalize_text(r.identifier)
            if norm:
                r.identifier_enc = crypto.encrypt(norm, "user_identity.identifier")
                r.identifier_idx = indexer.compute("user_identity.identifier", norm)
                needs_update = True
                
        if r.identifier_key_version != kv:
            r.identifier_key_version = kv
            needs_update = True
            
        if needs_update:
            await r.save(update_fields=["identifier_enc", "identifier_idx", "identifier_key_version"])
            migrated += 1
        
    logger.info(f"Scanned batch of {len(records)} UserIdentities. Updated: {migrated}")

async def backfill_person_email(kv: int, crypto: CryptoService, indexer: BlindIndexer, batch_size: int, delay: float):
    logger.info("--- Backfilling PersonEmail ---")
    records = await PersonEmail.all()
    
    migrated = 0
    for r in records:
        needs_update = False
        
        if r.email and not r.email_enc:
            norm = normalize_email(r.email)
            if norm:
                r.email_enc = crypto.encrypt(norm, "person_email.email")
                r.email_idx = indexer.compute("person_email.email", norm)
                needs_update = True
                
        if r.email_key_version != kv:
            r.email_key_version = kv
            needs_update = True
            
        if needs_update:
            await r.save(update_fields=["email_enc", "email_idx", "email_key_version"])
            migrated += 1
        
    logger.info(f"Scanned batch of {len(records)} PersonEmails. Updated: {migrated}")

async def backfill_person_contact(kv: int, crypto: CryptoService, indexer: BlindIndexer, batch_size: int, delay: float):
    logger.info("--- Backfilling PersonContact ---")
    records = await PersonContact.all().prefetch_related("contact_type")
    
    migrated = 0
    for r in records:
        needs_update = False
        
        if r.value and not r.value_enc:
            slug = r.contact_type.slug.lower() if r.contact_type and hasattr(r.contact_type, 'slug') else ""
            
            if "phone" in slug or "mobile" in slug or "telefone" in slug or "telemovel" in slug:
                norm_func = normalize_phone
            elif "email" in slug:
                norm_func = normalize_email
            else:
                norm_func = normalize_text
                
            norm = norm_func(r.value)
            if norm:
                r.value_enc = crypto.encrypt(norm, "person_contact.value")
                r.value_idx = indexer.compute("person_contact.value", norm)
                needs_update = True
                
        if r.value_key_version != kv:
            r.value_key_version = kv
            needs_update = True
            
        if needs_update:
            await r.save(update_fields=["value_enc", "value_idx", "value_key_version"])
            migrated += 1
        
    logger.info(f"Scanned batch of {len(records)} PersonContacts. Updated: {migrated}")

async def backfill_user_company(kv: int, crypto: CryptoService, indexer: BlindIndexer, batch_size: int, delay: float):
    logger.info("--- Backfilling UserCompany ---")
    records = await UserCompany.all()
    
    migrated = 0
    for r in records:
        needs_update = False
        
        if r.employee_number and not r.employee_number_enc:
            norm = normalize_text(r.employee_number)
            if norm:
                r.employee_number_enc = crypto.encrypt(norm, "user_company.employee_number")
                r.employee_number_idx = indexer.compute("user_company.employee_number", norm)
                needs_update = True
                
        if r.employee_number_key_version != kv:
            r.employee_number_key_version = kv
            needs_update = True
            
        if needs_update:
            await r.save(update_fields=["employee_number_enc", "employee_number_idx", "employee_number_key_version"])
            migrated += 1
        
    logger.info(f"Scanned batch of {len(records)} UserCompanies. Updated: {migrated}")

if __name__ == "__main__":
    try:
        asyncio.run(run_backfill(batch_size=500, delay=0.1))
    except KeyboardInterrupt:
        logger.info("Backfill interrupted by user.")
