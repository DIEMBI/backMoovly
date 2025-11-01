from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [

    # Utilisateurs CRUD
    path('utilisateurs/', views.list_utilisateurs, name='list-utilisateurs'),
    path('utilisateurs/<int:pk>/', views.get_utilisateur, name='get-utilisateur'),
    path('utilisateurs/<int:pk>/update/', views.update_utilisateur, name='update-utilisateur'),
    path('utilisateurs/<int:pk>/delete/', views.delete_utilisateur, name='delete-utilisateur'),

    # Roles CRUD
    path('roles/', views.list_roles, name='list-roles'),
    path('roles/create/', views.create_role, name='create-role'),

    # Profils CRUD
    path('profils/', views.list_profils, name='list-profils'),
    path('profils/create/', views.create_profil, name='create-profil'),

    # AUTHENTIFICATION

    # users
    path('users/create/', views.create_user, name='create-user'),

    # auth flow
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # simplejwt

    # password
    path('auth/forgot-password/', views.forgot_password, name='forgot-password'),
    path('auth/reset-password/', views.reset_password, name='reset-password'),
    path('auth/update-password/', views.update_password, name='update-password'),

    # user management
    path('users/<int:user_id>/status/', views.activate_or_deactivate, name='activate-deactivate'),
    path('users/<int:user_id>/roles/', views.assign_roles, name='assign-roles'),
]