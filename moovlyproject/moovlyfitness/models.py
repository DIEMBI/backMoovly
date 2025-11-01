from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UtilisateurManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("Le username est obligatoire")
        if not email:
            raise ValueError("L'email est obligatoire")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra_fields)


class Role(models.Model):
    nom = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.nom


class Profil(models.Model):
    poids = models.FloatField(null=True, blank=True)
    taille = models.FloatField(null=True, blank=True)
    objectifs = models.TextField(null=True, blank=True)
    preferences = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "profils"

    def __str__(self):
        return f"Profil {self.id}"


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    nom = models.CharField(max_length=50, blank=True)
    prenom = models.CharField(max_length=50, blank=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=191, unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    profil = models.OneToOneField(Profil, on_delete=models.CASCADE, null=True, blank=True)
    roles = models.ManyToManyField(Role)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    reset_token = models.TextField(null=True, blank=True)
    reset_token_expir = models.DateTimeField(null=True, blank=True)

    objects = UtilisateurManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "utilisateurs"

    def __str__(self):
        return self.username
