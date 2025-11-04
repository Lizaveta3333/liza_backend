import bcrypt

def _truncate_to_72_bytes(password: str) -> bytes:
    """
    Truncate password to exactly 72 bytes (bcrypt limit).
    Returns bytes for direct use with bcrypt.
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Passwords longer than 72 bytes are automatically truncated.
    """
    password_bytes = _truncate_to_72_bytes(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    Passwords longer than 72 bytes are automatically truncated.
    """
    password_bytes = _truncate_to_72_bytes(plain_password)
    if isinstance(hashed_password, str):
        hashed_bytes = hashed_password.encode('utf-8')
    else:
        hashed_bytes = hashed_password
    return bcrypt.checkpw(password_bytes, hashed_bytes)
