from datetime import datetime

from response.core.models import Action, Event
from response.core.serializers import ActionSerializer

from django.db.models.signals import pre_save
from django.dispatch import receiver

import logging
logger = logging.getLogger(__name__)


#@receiver(pre_save, sender=Action)
def emit_action_event(sender, instance: Action, **kwargs):

    logger.info(f"emitting event for action {instance}")

    try:
        prev_state = Action.objects.get(pk=instance.pk)
    except Action.DoesNotExist:
        event_type = "action_created"
        event_payload = ActionSerializer(instance).data
        event = Event()
        event.event_type = event_type
        event.set_payload(event_payload)
        event.timestamp = datetime.now(tz=None)
        event.save()
    else:
        # Action exists, so it's being updated
        event_type = None
        event_payload = {}
        if instance.details != prev_state.details:
            event_payload["details"] = instance.details
            event_type = "action_updated"
        if instance.user != prev_state.user:
            event_payload["user"] = instance.user.serialize()
            event_type = "action_updated"
        if instance.done and not prev_state.done:
            event_payload["done"] = True
            event_type = "action_completed"

        # don't emit anything if action is unchanged

        # write the event to the table
        event = Event()
        event.event_type = event_type
        event.set_payload(event_payload)
        event.timestamp = datetime.now(tz=None)
        event.save()


pre_save.connect(emit_action_event, sender=Action)