# myapp/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ContactMessage
from utils.email_utils import (
    send_contact_form_confirmation,
    forward_contact_form_to_admin
)

@receiver(post_save, sender=ContactMessage)
def handle_contact_message(sender, instance, created, **kwargs):
    if created:
        contact_data = {
            'name': instance.name,
            'email': instance.email,
            'message': instance.message,
        }

        # Send confirmation to user
        send_contact_form_confirmation(contact_data)

        # Forward to admins
        forward_contact_form_to_admin(contact_data)
