from django.core.management.base import BaseCommand

from ...services import trigger_reminders


class Command(BaseCommand):
    help = "Trigger reminder deliveries for due user-alert preferences"

    def handle(self, *args, **options):
        count = trigger_reminders()
        self.stdout.write(self.style.SUCCESS(f"Triggered {count} reminders"))


