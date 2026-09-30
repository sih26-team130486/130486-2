"""
management/commands/seed_demo.py
Run: python manage.py seed_demo

Creates 3 demo users (admin / IO / court) for the SIH presentation.
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser


DEMO_USERS = [
    {
        'username':  'admin',
        'email':     'admin@pramaan.gov.in',
        'full_name': 'System Administrator',
        'role':      'ADMIN',
        'password':  'Admin@1234',
    },
    {
        'username':  'inspector_sharma',
        'email':     'inspector.sharma@pramaan.gov.in',
        'full_name': 'Inspector Sharma',
        'role':      'IO',
        'password':  'IO@12345',
    },
    {
        'username':  'court_user',
        'email':     'court@pramaan.gov.in',
        'full_name': 'Anita Rao (Prosecutor)',
        'role':      'COURT',
        'password':  'Court@1234',
    },
]


class Command(BaseCommand):
    help = 'Seed demo users for PRAMAAN SIH presentation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n[*] Seeding PRAMAAN demo users...\n'))

        for user_data in DEMO_USERS:
            username = user_data['username']
            if CustomUser.objects.filter(username=username).exists():
                self.stdout.write(f'  [SKIP] User "{username}" already exists.')
                continue

            user = CustomUser.objects.create_user(
                username  = user_data['username'],
                email     = user_data['email'],
                full_name = user_data['full_name'],
                role      = user_data['role'],
                password  = user_data['password'],
                is_staff  = (user_data['role'] == 'ADMIN'),
                is_superuser = (user_data['role'] == 'ADMIN'),
            )
            self.stdout.write(
                self.style.SUCCESS(f'  [OK] Created [{user.role}] {user.full_name} -> {username}')
            )

        self.stdout.write(self.style.SUCCESS('\n[DONE] Demo seed complete!\n'))
        self.stdout.write('-' * 50)
        self.stdout.write('  Login credentials:')
        for u in DEMO_USERS:
            self.stdout.write(f'  [{u["role"]:5}] username: {u["username"]:20} password: {u["password"]}')
        self.stdout.write('-' * 50 + '\n')

