import bcrypt
from .db import Database


class UsersDAO:
    """Data Access Object for User operations"""

    @staticmethod
    async def get_user_by_email(conn, email: str):
        """Get a user by email"""
        query = """
        SELECT user_id, name, email, password_hash, role, phone_number, address, birthday 
        FROM USERS 
        WHERE email = $1
        """
        return await Database.fetchrow(conn, query, email)

    @staticmethod
    async def get_user_by_id(conn, user_id: str):
        """Get a user by ID"""
        query = """
        SELECT user_id, name, email, phone_number, address, birthday, role
        FROM USERS 
        WHERE user_id = $1
        """
        return await Database.fetchrow(conn, query, user_id)

    @staticmethod
    async def create_user(conn, name: str, email: str, password: str, phone_number=None, address=None, birthday=None,
                          role="consumer"):
        """Create a new user"""
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        query = """
        INSERT INTO USERS (name, email, password_hash, phone_number, address, birthday, role)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING user_id, name, email, role
        """
        return await Database.fetchrow(
            conn,
            query,
            name,
            email,
            password_hash,
            phone_number,
            address,
            birthday,
            role
        )

    @staticmethod
    async def verify_password(stored_password_hash: str, password: str) -> bool:
        """Verify a password against a hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            stored_password_hash.encode('utf-8')
        )
