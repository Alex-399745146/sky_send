# users/context_processors.py

from django.contrib.auth.models import Group


def role_flags(request):
    user = request.user
    is_manager = user.is_authenticated and (user.is_superuser or user.groups.filter(name="manager").exists())
    return {"is_manager": is_manager}
