from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Utilisateur, Profil, Role
from .serializers import UtilisateurSerializer, ProfilSerializer, RoleSerializer
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.utils.timezone import now, timedelta
from django.contrib.auth.hashers import check_password
import uuid
from django.contrib.auth import authenticate, login as django_login, logout as django_logout, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import Utilisateur, Role
from .serializers import UtilisateurDetailSerializer






@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def list_utilisateurs(request):
    utilisateurs = Utilisateur.objects.all()
    serializer = UtilisateurSerializer(utilisateurs, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_utilisateur(request, pk):
    try:
        utilisateur = Utilisateur.objects.get(pk=pk)
    except Utilisateur.DoesNotExist:
        return JsonResponse({'message': 'Utilisateur introuvable'}, status=404)

    serializer = UtilisateurSerializer(utilisateur)
    return JsonResponse(serializer.data)


@api_view(['PUT'])
# @permission_classes([IsAuthenticated])
def update_utilisateur(request, pk):
    try:
        utilisateur = Utilisateur.objects.get(pk=pk)
    except Utilisateur.DoesNotExist:
        return JsonResponse({'message': 'Utilisateur introuvable'}, status=404)

    data = JSONParser().parse(request)
    serializer = UtilisateurSerializer(utilisateur, data=data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data)

    return JsonResponse(serializer.errors, status=400)


@api_view(['DELETE'])
# @permission_classes([IsAuthenticated])
def delete_utilisateur(request, pk):
    try:
        utilisateur = Utilisateur.objects.get(pk=pk)
    except Utilisateur.DoesNotExist:
        return JsonResponse({'message': 'Utilisateur introuvable'}, status=404)

    utilisateur.delete()
    return JsonResponse({'message': 'Utilisateur supprimé avec succès'})




@api_view(['GET'])
def list_roles(request):
    roles = Role.objects.all()
    serializer = RoleSerializer(roles, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['POST'])
def create_role(request):
    data = JSONParser().parse(request)
    serializer = RoleSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data, status=201)

    return JsonResponse(serializer.errors, status=400)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def list_profils(request):
    profils = Profil.objects.all()
    serializer = ProfilSerializer(profils, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def create_profil(request):
    data = JSONParser().parse(request)
    serializer = ProfilSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data, status=201)

    return JsonResponse(serializer.errors, status=400)



# ---------- UTIL ----------

def create_jwt_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

# ---------- REGISTER / CREATE USER (avec roles ids) ----------
@api_view(['POST'])
@permission_classes([AllowAny])
def create_user(request):
    data = request.data.copy()
    roles_ids = data.pop('roles', [])
    serializer = UtilisateurSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        if roles_ids:
            roles = Role.objects.filter(id__in=roles_ids)
            user.roles.set(roles)
        return Response(UtilisateurDetailSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------- LOGIN (username + password) ----------
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'message': "Cet utilisateur n'esxiste pas dans la base de donnée"}, status=status.HTTP_401_UNAUTHORIZED)

    # Vérifier le mot de passe
    if not user.check_password(password):
        return Response({'message': 'Mot de passe incorrecte'}, status=status.HTTP_401_UNAUTHORIZED)

    # Vérifier si le compte est actif
    if not user.is_active:
        return Response({'message': 'Compte désactivé'}, status=status.HTTP_403_FORBIDDEN)

    # Générer tokens
    tokens = create_jwt_for_user(user)

    # Stockage des tokens si nécessaire
    user.access_token = tokens['access']
    user.refresh_token = tokens['refresh']
    user.reset_token_expir = now() + timedelta(hours=24)
    user.save()

    user_data = UtilisateurSerializer(user).data
    return Response({
        'message': 'Connexion réussie',
        'user': user_data,
        'access_token': tokens['access'],
        'refresh_token': tokens['refresh'],
        'reset_token_expir': user.reset_token_expir,
    })

# ---------- REFRESH TOKEN endpoint (on peut utiliser TokenRefreshView de simplejwt) ----------
from rest_framework_simplejwt.views import TokenRefreshView
# (Tu peux inclure TokenRefreshView directement dans urls.py, pas besoin de reimplementer)

# DECCONNEXION
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # Blacklist refresh token si utilisé
    refresh_token = request.data.get('refresh_token')
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass

    # Déconnexion Django session
    django_logout(request)

    # Supprimer tokens seulement si user authentifié
    user = request.user
    if user and user.is_authenticated:
        user.access_token = None
        user.refresh_token = None
        user.save()

    return Response({'message': 'Déconnexion réussie'})

# ---------- FORGOT PASSWORD (génère reset token, envoie email) ----------
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = Utilisateur.objects.get(email=email)
    except Utilisateur.DoesNotExist:
        return Response({'message': 'Aucun utilisateur avec cet email'}, status=status.HTTP_404_NOT_FOUND)

    # token classique Django + uid encoded
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = f"{request.scheme}://{request.get_host()}/api/auth/reset-password/?uid={uid}&token={token}"

    # Sauvegarde facultative d'un reset_token dans DB
    user.reset_token = token
    user.reset_token_expir = now() + timedelta(hours=1)
    user.save()

    # Envoyer l'email
    subject = "Réinitialisation de mot de passe - Moovly"
    message = f"Bonjour {user.nom or user.username},\n\nClique sur le lien pour réinitialiser ton mot de passe:\n{reset_url}\n\nSi tu n'as pas demandé ça, ignore ce message."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

    return Response({'detail': 'Email de réinitialisation envoyé'})


# ---------- RESET PASSWORD (via POST body or via link GET) ----------
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    uid = request.data.get('uid') or request.query_params.get('uid')
    token = request.data.get('token') or request.query_params.get('token')
    new_password = request.data.get('new_password')

    if not uid or not token or not new_password:
        return Response({'message': 'uid, token et new_password requis'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        uid_decoded = force_str(urlsafe_base64_decode(uid))
        user = Utilisateur.objects.get(pk=uid_decoded)
    except Exception:
        return Response({'message': 'Lien invalide'}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifier le token Django
    if not default_token_generator.check_token(user, token):
        return Response({'message': 'Token invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

    # Optionnel vérifier expiration si stocké
    if user.reset_token_expir and now() > user.reset_token_expir:
        return Response({'message': 'Token expiré'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expir = None
    user.save()
    return Response({'message': 'Mot de passe réinitialisé'})


# ---------- UPDATE PASSWORD (user connecté) ----------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    if not user.check_password(old_password):
        return Response({'message': 'Ancien mot de passe incorrect'}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save()
    return Response({'message': 'Mot de passe mis à jour'})


# ---------- ACTIVATE / DEACTIVATE user ----------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])  # adapte selon tes règles
def activate_or_deactivate(request, user_id):
    try:
        user = Utilisateur.objects.get(pk=user_id)
    except Utilisateur.DoesNotExist:
        return Response(
            {'message': 'Utilisateur introuvable'},
            status=status.HTTP_404_NOT_FOUND
        )

    active = request.data.get('active')  # ✅ on change le nom ('active')

    # Accepte true/false ou 'true'/'false'
    if isinstance(active, str):
        active = active.lower() == 'true'

    if active not in [True, False]:
        return Response(
            {'message': "Champ 'active' invalide (true/false)"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Le SEUL champ géré = is_active
    user.is_active = active
    user.save()

    return Response({
        'message': 'Utilisateur activé' if active else 'Utilisateur désactivé'
    })


# ---------- UTIL: assigner/retirer rôle (endpoints helper) ----------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_roles(request, user_id):
    try:
        user = Utilisateur.objects.get(pk=user_id)
    except Utilisateur.DoesNotExist:
        return Response({'message': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

    roles_ids = request.data.get('roles', [])
    roles = Role.objects.filter(id__in=roles_ids)
    user.roles.set(roles)
    return Response(UtilisateurDetailSerializer(user).data)