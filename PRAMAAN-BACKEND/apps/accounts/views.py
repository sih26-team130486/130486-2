"""
accounts/views.py — Auth views: Login, Register, Profile, User list, Logout
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import CustomUser
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .permissions import IsAdmin
from apps.audit.utils import log_action


class LoginView(APIView):
    """POST /api/v1/auth/login/ — Get JWT tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        # Audit log
        log_action(
            user=user,
            action='LOGIN',
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={'username': user.username, 'role': user.role}
        )

        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — Blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            log_action(
                user=request.user,
                action='LOGOUT',
                result='SUCCESS',
                severity='INFO',
                ip_address=get_client_ip(request),
            )
            return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — Create user (ADMIN only)."""
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        log_action(
            user=request.user,
            action='CREATE_USER',
            result='SUCCESS',
            severity='INFO',
            ip_address=get_client_ip(request),
            metadata={'created_user': user.username, 'role': user.role}
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class ProfileView(APIView):
    """GET /api/v1/auth/profile/ — Get or update own profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            # Prevent self-role escalation for non-admins
            if 'role' in request.data and not request.user.is_admin:
                return Response({'error': 'You cannot change your own role.'}, status=status.HTTP_403_FORBIDDEN)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    """GET /api/v1/auth/users/ — List all users (ADMIN only)."""
    permission_classes = [IsAdmin]

    def get(self, request):
        users = CustomUser.objects.all().order_by('-created_at')
        return Response(UserSerializer(users, many=True).data)


class UserDetailView(APIView):
    """GET/PATCH/DELETE /api/v1/auth/users/<id>/ — Manage single user (ADMIN only)."""
    permission_classes = [IsAdmin]

    def get_object(self, pk):
        try:
            return CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)

    def patch(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        user.is_active = False
        user.save()
        return Response({'detail': 'User deactivated.'}, status=status.HTTP_200_OK)


def get_client_ip(request):
    """Extract real client IP from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')
