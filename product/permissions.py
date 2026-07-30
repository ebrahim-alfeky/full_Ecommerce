from rest_framework import permissions

class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    أي حد يقدر يشوف (GET),
    فقط السوبر يوزر يقدر يضيف/يعدل/يمسح.
    """
    def has_permission(self, request, view):
        # أي عملية قراءة → السماح لأي حد
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # أي عملية تعديل/إضافة/حذف → بس السوبر يوزر
        return request.user and request.user.is_superuser
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    أي حد يقدر يشوف (GET),
    فقط المالك يقدر يعدل أو يمسح.
    """
    def has_object_permission(self, request, view, obj):
        # أي عملية قراءة → السماح لأي حد
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # أي عملية تعديل/حذف → بس المالك
        return obj.owner == request.user