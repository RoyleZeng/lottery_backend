from fastapi import HTTPException, status
from typing import Dict, Any
from asyncpg import UniqueViolationError
from lottery_api.data_access_object.users_dao import UsersDAO
from lottery_api.lib.auth_library.jwt import JwtToken, JWTKey
from lottery_api.lib.auth_library.permission import Auth
from lottery_api.schema.auth import RegisterRequest, LoginRequest


class AuthBusiness:
    """Business logic for authentication operations"""
    
    @staticmethod
    async def register_user(conn, request: RegisterRequest) -> Dict[str, Any]:
        """Register a new consumer account"""
        try:
            # Check if user with this email already exists
            existing_user = await UsersDAO.get_user_by_email(conn, request.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists"
                )

            # Create the user
            user = await UsersDAO.create_user(
                conn,
                name=request.name,
                email=request.email,
                password=request.password,
                phone_number=request.phone_number,
                address=request.address,
                birthday=request.birthday
            )

            return {
                "user_id": str(user["user_id"]),
                "email": user["email"],
                "name": user["name"],
                "role": user["role"]
            }
        except UniqueViolationError:
            # This catches if there's a race condition between checking and inserting
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or phone number already exists"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    @staticmethod
    async def login_user(conn, request: LoginRequest) -> Dict[str, Any]:
        """Login a user and return JWT token"""
        # Find the user
        user = await UsersDAO.get_user_by_email(conn, request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect"
            )

        # Verify password
        if not await UsersDAO.verify_password(user["password_hash"], request.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect"
            )

        # Convert UUID to string before serializing to JSON
        access_token = JwtToken(key=JWTKey()).generate_token(
            claims={
                "user_id": str(user["user_id"]),  # Convert UUID to string
                "username": user["name"],
                "roles": user["role"],
                "attributes": [],
            })

        return {
            "access_token": access_token,
            "user": {
                "user_id": str(user["user_id"]),
                "email": user["email"],
                "name": user["name"],
                "role": user["role"]
            }
        }
    
    @staticmethod
    async def get_current_user_info(conn, auth: Auth) -> Dict[str, Any]:
        """Get information about the currently logged-in user"""
        user = await UsersDAO.get_user_by_id(conn, auth.user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "user_id": str(user["user_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "phone_number": user["phone_number"],
            "address": user["address"],
            "birthday": user["birthday"]
        } 