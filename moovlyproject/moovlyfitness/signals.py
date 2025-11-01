from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Role

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    if sender.name == "moovlyfitness":
        roles = ["admin", "free", "abonne"]
        for r in roles:
            Role.objects.get_or_create(nom=r)