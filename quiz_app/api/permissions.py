from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Allow access to an object only for the user who owns it."""

    def has_object_permission(self, request, view, obj):
        """Return True if the requesting user owns the given object."""
        return request.user == obj.user
