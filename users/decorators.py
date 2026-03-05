from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """
    Decorator that restricts a view to users with one of the specified roles.
    Usage: @role_required('admin') or @role_required('donor', 'admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("users:login")
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect("users:dashboard")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    return role_required("admin")(view_func)


def donor_required(view_func):
    return role_required("donor")(view_func)


def hospital_required(view_func):
    return role_required("hospital")(view_func)
