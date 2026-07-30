from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    صلاحيات للعناوين:
    - المشاهدة: صاحب العنوان فقط
    - الإضافة: أي مستخدم مسجل دخول
    - التعديل: فقط صاحب العنوان
    - الحذف: صاحب العنوان أو الادمن
    """
    
    def has_permission(self, request, view):
        # Add (create) => أي مستخدم مسجل دخول
        if view.action == 'create':
            return request.user and request.user.is_authenticated
        # List => أي مستخدم مش هينفع يشوف غير عناوينه، ده handled by get_queryset
        return True

    def has_object_permission(self, request, view, obj):
        # Retrieve (view) => صاحب العنوان فقط
        if view.action in ['retrieve', 'list']:
            return obj.user == request.user

        # Update / Partial update => صاحب العنوان فقط
        if view.action in ['update', 'partial_update']:
            return obj.user == request.user

        # Delete => صاحب العنوان أو الادمن
        if view.action == 'destroy':
            return obj.user == request.user or request.user.is_staff

        return False
