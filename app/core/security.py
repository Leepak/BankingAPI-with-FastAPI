from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ---------- PASSWORD HASH ----------
def hash_password(password: str) -> str:
    # bcrypt limitation fix
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password too long (bcrypt max 72 bytes)")

    return pwd_context.hash(password)


# ---------- VERIFY PASSWORD ----------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)