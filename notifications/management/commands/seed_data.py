from django.core.management.base import BaseCommand

from ...models import Team, User


class Command(BaseCommand):
    help = "Seed initial teams and users for testing"

    def handle(self, *args, **options):
        teams = [
            ("Engineering"),
            ("Marketing"),
            ("Sales"),
        ]
        team_objs = {}
        for name in teams:
            team, _ = Team.objects.get_or_create(name=name)
            team_objs[name] = team

        users = [
            ("admin", "admin@example.com", "Engineering", True),
            ("alice", "alice@example.com", "Engineering", False),
            ("bob", "bob@example.com", "Marketing", False),
            ("carol", "carol@example.com", "Sales", False),
        ]

        for username, email, team_name, is_staff in users:
            user, created = User.objects.get_or_create(username=username, defaults={
                "email": email,
                "team": team_objs[team_name],
                "is_staff": is_staff,
                "is_superuser": is_staff,
            })
            if created:
                user.set_password("password")
                user.save()

        self.stdout.write(self.style.SUCCESS("Seeded teams and users (password: password)"))


