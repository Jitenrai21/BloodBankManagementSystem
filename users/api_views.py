from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from .models import User


class RegisterAPIView(APIView):
    """POST /api/auth/register/ — create a new user account."""
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        required = ["email", "password", "role"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return Response(
                {"error": f"Missing fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if data["role"] not in [User.DONOR, User.HOSPITAL]:
            return Response(
                {"error": "role must be 'donor' or 'hospital'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(email=data["email"]).exists():
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_409_CONFLICT,
            )
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            phone=data.get("phone", ""),
            role=data["role"],
        )
        user.is_approved = data["role"] == User.DONOR
        user.save()
        return Response(
            {
                "message": "Account created successfully.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "is_approved": user.is_approved,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    """POST /api/auth/login/ — authenticate and open session."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response(
                {"error": "email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"error": "Account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not user.is_approved and user.role == User.HOSPITAL:
            return Response(
                {"error": "Hospital account pending admin approval."},
                status=status.HTTP_403_FORBIDDEN,
            )
        login(request, user)
        return Response(
            {
                "message": "Login successful.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "dashboard_url": "/users/dashboard/",
                },
            }
        )


class LogoutAPIView(APIView):
    """POST /api/auth/logout/ — destroy session."""

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."})


class MeAPIView(APIView):
    """GET /api/auth/me/ — return current authenticated user info."""

    def get(self, request):
        u = request.user
        return Response(
            {
                "id": u.id,
                "email": u.email,
                "phone": u.phone,
                "role": u.role,
                "is_approved": u.is_approved,
                "date_joined": u.date_joined,
            }
        )
