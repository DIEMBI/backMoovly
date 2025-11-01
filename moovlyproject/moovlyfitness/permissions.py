from rest_framework import permissions

class IsRole(permissions.BasePermission):
    """
    Vérifie que l'utilisateur a au moins un des rôles fournis via allowed_roles attribute on view.
    Usage: @permission_classes([IsRole]) et définir view.allowed_roles = ['admin']
    Or create small wrapper views that pass allowed roles.
    """

    def has_permission(self, request, view):
        allowed = getattr(view, 'allowed_roles', None)
        if not allowed:
            return True  # si rien défini, on autorise (ou tu peux return False pour être strict)
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.roles.filter(nom__in=allowed).exists()