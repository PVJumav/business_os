import argparse
import getpass

from backend.api.auth import _hash_password
from backend.core.create_tables import create_tables
from backend.core.database import SessionLocal
from backend.models.auth import AuthUser


def upsert_admin(email: str, password: str, full_name: str):
    create_tables()
    db = SessionLocal()
    try:
        user = db.query(AuthUser).filter(AuthUser.email == email).first()
        if user:
            user.full_name = full_name
            user.role = "admin"
            user.hashed_password = _hash_password(password)
            user.is_active = True
            action = "updated"
        else:
            user = AuthUser(
                email=email,
                full_name=full_name,
                role="admin",
                hashed_password=_hash_password(password),
                is_active=True,
            )
            db.add(user)
            action = "created"

        db.commit()
        print(f"Admin user {action}: {email}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Create or promote a BusinessOS admin user.")
    parser.add_argument("--email", default="admin@businessos.com")
    parser.add_argument("--full-name", default="BusinessOS Admin")
    parser.add_argument("--password")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Admin password: ")
    if len(password) < 6:
        raise SystemExit("Password must be at least 6 characters.")

    upsert_admin(args.email, password, args.full_name)


if __name__ == "__main__":
    main()
