"""
accounts/models.py — Custom User with Role-Based Access Control
Roles: ADMIN | IO (Investigating Officer) | COURT
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('IO',    'Investigating Officer'),
        ('COURT', 'Court / Prosecutor'),
    ]

    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username  = models.CharField(max_length=150, unique=True)
    email     = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    role      = models.CharField(max_length=10, choices=ROLE_CHOICES, default='IO')
    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'pramaan_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.full_name or self.username} [{self.role}]'

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    @property
    def is_io(self):
        return self.role == 'IO'

    @property
    def is_court(self):
        return self.role == 'COURT'
