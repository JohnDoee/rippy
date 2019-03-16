from django.core.management.base import BaseCommand, CommandError

from ...models import Job


class Command(BaseCommand):
    help = 'Cleanup job with an active status, can be used after rippy has been shut down'

    def handle(self, *args, **options):
        Job.objects.exclude(status__in=[Job.SUCCESS, Job.FAILED, Job.CANCELLED]) \
                   .update(status=Job.FAILED, status_message='Job cleaned up')
