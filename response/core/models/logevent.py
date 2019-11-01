import json

from django.contrib.postgres.fields import JSONField

from django.db import models

# We could use Choices here, but need to think about how it's serialized
EVENT_TYPE_INCIDENT_CREATED = "incident_created"
EVENT_TYPE_INCIDENT_UPDATED = "incident_updated"
EVENT_TYPE_INCIDENT_CLOSED = "incident_closed"

EVENT_TYPE_ACTION_CREATED = "action_created"
EVENT_TYPE_ACTION_UPDATED = "action_updated"
EVENT_TYPE_ACTION_COMPLETED = "action_completed"


class LogEvent(models.Model):

    timestamp = models.DateTimeField()
    event_type = models.CharField(max_length=50)
    payload = JSONField()

    def set_payload(self, payload_obj):
        self.payload = json.dumps(payload_obj)
