from django.apps import AppConfig

class MoovlyfitnessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moovlyfitness'

    def ready(self):
        import moovlyfitness.signals