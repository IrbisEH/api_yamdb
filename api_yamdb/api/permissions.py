from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAppAdminOrSuperUser(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == "admin" or bool(request.user.is_staff):
                return True
        else:
            return False


class CustomPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        if request.method == "POST":
            return bool(
                request.user.is_authenticated and request.user.role == "admin"
            )


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):

        if request.method in SAFE_METHODS:
            return True

        return bool(
            request.user.is_authenticated and request.user.role == "admin"
        )


class ReviewCommentPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        if request.method == "POST":
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        if request.method == "GET":
            return True
        if request.user.is_authenticated and (
            request.user.role == "admin" or request.user.role == "moderator"
        ):
            return True
        if request.method == ("PATCH" or "DELETE"):
            return obj.author == request.user
