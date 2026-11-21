from .models import HouseImage, RoomImage
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os


@receiver(post_delete, sender=HouseImage)
def delete_house_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

@receiver(post_delete, sender=RoomImage)
def delete_room_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)