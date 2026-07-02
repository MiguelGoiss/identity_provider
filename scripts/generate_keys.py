import base64
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, constants

def generate_keys():
  print("--- Generating 2048-bit RSA Key Pair ---")
  
  # 1. Generate Private Key
  private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
  )

  # 2. Serialize Private Key (PEM)
  pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
  )

  # 3. Serialize Public Key (PEM)
  public_key = private_key.public_key()
  pem_public = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
  )

  # 4. Create JWK (JSON Web Key) for the Public Key
  # We use python-jose to do the heavy lifting of calculating 'n' and 'e'
  key_id = "auth-key-1" # Rotate this string if you ever change keys!
  jwk_dict = jwk.construct(pem_public.decode('utf-8'), algorithm=constants.ALGORITHMS.RS256).to_dict()
  jwk_dict["kid"] = key_id
  jwk_dict["use"] = "sig"
  
  # 5. Create JWKS (The set)
  jwks = {"keys": [jwk_dict]}

  # --- OUTPUT ---
  
  print("\n[ACTION REQUIRED] 1. Save this JSON as 'jwks.json' in your Auth Service root (or serve from memory):")
  print("-" * 20)
  print(json.dumps(jwks, indent=2))
  print("-" * 20)

  print("\n[ACTION REQUIRED] 2. Add this line to your Auth Service .env file:")
  print("(I have Base64 encoded it to avoid newline issues in .env files)")
  print("-" * 20)
  b64_private_key = base64.b64encode(pem_private).decode('utf-8')
  print(f"AUTH_PRIVATE_KEY={b64_private_key}")
  print(f"AUTH_KEY_ID={key_id}")
  print("-" * 20)

if __name__ == "__main__":
  generate_keys()