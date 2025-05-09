import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files import File
from django.conf import settings
from .models import StudentProfile, StudentRequest

@receiver(post_save, sender=StudentRequest)
def create_student_profile(sender, instance, created=False, **kwargs):
    """Create a student profile when a student request is approved"""
    if not created and instance.approved:
        # Check if profile already exists for the user
        if not hasattr(instance.user, 'studentprofile'):
            # Create the StudentProfile
            profile = StudentProfile.objects.create(user=instance.user)
            
            # Ensure the default profile picture is copied from static to media if it doesn't exist
            default_profile_picture = os.path.join(settings.BASE_DIR, 'static', 'profile_pictures', 'default.png')
            media_profile_picture = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', 'default.png')

            if not os.path.exists(media_profile_picture):
                # Copy the default profile picture to the media folder
                with open(default_profile_picture, 'rb') as f:
                    profile.profile_picture.save('default.png', File(f), save=True)
