import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class Job(models.Model):
    url = models.URLField(max_length=5000)

    PENDING = "pending"
    PARSING = "parsing"
    DOWNLOADING = "downloading"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING = "waiting"
    CANCELLED = "cancelled"
    status = models.CharField(
        max_length=20,
        choices=(
            (PENDING, "Pending"),
            (PARSING, "Parsing"),
            (DOWNLOADING, "Downloading"),
            (SUCCESS, "Success"),
            (FAILED, "Failed"),
            (WAITING, "Waiting for user-input"),
            (CANCELLED, "Cancelled"),
        ),
        default=PENDING,
    )
    status_message = models.CharField(max_length=2000, blank=True, default="")

    path = models.FileField(null=True)
    name = models.CharField(max_length=500, null=True)

    hidden = models.BooleanField(default=False)
    scheduled = models.BooleanField(default=False)

    last_updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def send_event(self, event_type, **kwargs):
        kwargs["type"] = event_type
        kwargs["id"] = self.pk
        channel_layer = get_channel_layer()
        logger.debug("Sending event %r" % (kwargs,))
        async_to_sync(channel_layer.group_send)("event", kwargs)

    def send_progress_update(self, total, progress):
        self.send_event("job.progress", total=total, progress=progress)


@receiver(post_save, sender=Job)
def event_job_update(sender, instance, created, **kwargs):
    from .tasks import handle_job
    from .views import JobSerializer

    payload = JobSerializer(instance).data

    import threading

    def job_update():
        instance.send_event("job.update", **payload)

    threading.Thread(target=job_update).start()

    if not instance.scheduled:
        instance.scheduled = True
        instance.save()
        handle_job.delay(instance.pk)
