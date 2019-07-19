from django.conf import settings

from rest_framework import serializers, viewsets, views
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = (
            "id",
            "url",
            "status",
            "status_message",
            "path",
            "name",
            "hidden",
            "last_updated",
            "created",
        )


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(hidden=False)
    serializer_class = JobSerializer

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        job = self.get_object()
        job.status = job.CANCELLED
        job.save()
        return Response({"status": "job cancelled"})

    @action(detail=True, methods=["post"])
    def hide(self, request, pk=None):
        job = self.get_object()
        job.hidden = True
        job.save()
        return Response({"status": "job hidden"})

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        job = self.get_object()
        job.status = job.PENDING
        job.scheduled = False
        job.save()
        return Response({"status": "Retrying job"})


class ConfigView(views.APIView):
    def get(self, request):
        config = {}

        if settings.PARSE_BROWSER_URL:
            config["parse_browser_url"] = settings.PARSE_BROWSER_URL

        return Response(config)
