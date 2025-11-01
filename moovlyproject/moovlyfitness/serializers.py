from rest_framework import serializers
from .models import Utilisateur, Profil, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'nom']

class ProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profil
        fields = ['id', 'poids', 'taille', 'objectifs', 'preferences']
        

class UtilisateurSerializer(serializers.ModelSerializer):
    profil = ProfilSerializer(required=False)

    # ✅ Permet d'envoyer une liste d'IDs des rôles
    roles = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Role.objects.all(), required=False
    )
     

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'nom', 'prenom', 'username', 'email',
            'phone', 'password', 'profil', 'roles', 'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True},   # ✅ invisible dans les réponses API
            'is_active': {'read_only': True}    # ✅ modifiable uniquement via /activate-user/
        }

    def create(self, validated_data):
        profil_data = validated_data.pop('profil', None)

        # ✅ Récupérer les rôles envoyés
        roles_data = validated_data.pop('roles', [])

        password = validated_data.pop('password')
        user = Utilisateur.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # ✅ Ajouter les rôles ManyToMany
        if roles_data:
            user.roles.set(roles_data)

        # ✅ Créer profil s'il existe
        if profil_data:
            profil = Profil.objects.create(**profil_data)
            user.profil = profil
            user.save()

        return user

    def update(self, instance, validated_data):
        profil_data = validated_data.pop('profil', None)

        # ✅ Rôles reçus dans PUT/PATCH
        roles_data = validated_data.pop('roles', None)

        password = validated_data.pop('password', None)

        # ✅ Mise à jour des champs simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        # ✅ Mise à jour des rôles ManyToMany
        if roles_data is not None:
            instance.roles.set(roles_data)

        # ✅ Mise à jour profil
        if profil_data and instance.profil:
            for attr, value in profil_data.items():
                setattr(instance.profil, attr, value)
            instance.profil.save()

        return instance


class UtilisateurDetailSerializer(serializers.ModelSerializer):
    profil = ProfilSerializer()
    roles = RoleSerializer(many=True)

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'nom', 'prenom', 'username', 'email', 'phone',
            'is_active', 'profil', 'roles'
        ]
        read_only_fields = fields

        