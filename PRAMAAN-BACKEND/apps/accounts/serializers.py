"""
accounts/serializers.py — Auth serializers
"""
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile and listing."""
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'full_name', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user (ADMIN only)."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'full_name', 'role', 'password']

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Login with username + password, returns JWT tokens."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials. Please try again.')
        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')
        data['user'] = user
        return data


class TokenResponseSerializer(serializers.Serializer):
    """Response shape after successful login."""
    access  = serializers.CharField()
    refresh = serializers.CharField()
    user    = UserSerializer()
