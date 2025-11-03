from django.contrib import admin, messages
from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin.helpers import ActionForm
from typing import Any, cast


class UserActionForm(ActionForm):
    """Custom action form to select a Group or Permissions to apply to selected users."""

    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=False, label="Group to add/remove")
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(), required=False, label="Permissions to grant/revoke"
    )


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Extend the default User admin with convenient admin actions.

    Actions available in the list view (select users -> choose action):
    - add_to_group: add selected users to the chosen group (use ActionForm 'group')
    - remove_from_group: remove selected users from the chosen group
    - grant_permissions: add permission(s) to selected users (use ActionForm 'permissions')
    - revoke_permissions: remove permission(s) from selected users
    - promote_staff / demote_staff: set/unset is_staff flag
    - delete_users: delete selected accounts (skips superusers unless you are superuser)
    """

    action_form = UserActionForm
    actions = [
        "add_to_group",
        "remove_from_group",
        "grant_permissions",
        "revoke_permissions",
        "promote_staff",
        "demote_staff",
        "delete_users",
    ]

    def _ensure_requester_is_superuser(self, request):
        return request.user.is_superuser

    def add_to_group(self, request, queryset):
        group = request.POST.get("group")
        if not group:
            messages.error(request, "Please select a group in the action form.")
            return
        try:
            g = Group.objects.get(pk=group)
        except Group.DoesNotExist:
            messages.error(request, "Selected group does not exist.")
            return
        count = 0
        for user in queryset:
            if not user.groups.filter(pk=g.pk).exists():
                user.groups.add(g)
                count += 1
        messages.success(request, f"Added {count} user(s) to group '{g.name}'.")
    cast(Any, add_to_group).short_description = "Add selected users to group"

    def remove_from_group(self, request, queryset):
        group = request.POST.get("group")
        if not group:
            messages.error(request, "Please select a group in the action form.")
            return
        try:
            g = Group.objects.get(pk=group)
        except Group.DoesNotExist:
            messages.error(request, "Selected group does not exist.")
            return
        count = 0
        for user in queryset:
            if user.groups.filter(pk=g.pk).exists():
                user.groups.remove(g)
                count += 1
        messages.success(request, f"Removed {count} user(s) from group '{g.name}'.")
    cast(Any, remove_from_group).short_description = "Remove selected users from group"

    def grant_permissions(self, request, queryset):
        perms = request.POST.getlist("permissions")
        if not perms:
            messages.error(request, "Please select at least one permission in the action form.")
            return
        perms_qs = Permission.objects.filter(pk__in=perms)
        count = 0
        for user in queryset:
            for p in perms_qs:
                if not user.user_permissions.filter(pk=p.pk).exists():
                    user.user_permissions.add(p)
                    count += 1
        messages.success(request, f"Granted {count} permission assignments to selected users.")
    cast(Any, grant_permissions).short_description = "Grant selected permissions to users"

    def revoke_permissions(self, request, queryset):
        perms = request.POST.getlist("permissions")
        if not perms:
            messages.error(request, "Please select at least one permission in the action form.")
            return
        perms_qs = Permission.objects.filter(pk__in=perms)
        count = 0
        for user in queryset:
            for p in perms_qs:
                if user.user_permissions.filter(pk=p.pk).exists():
                    user.user_permissions.remove(p)
                    count += 1
        messages.success(request, f"Revoked {count} permission assignments from selected users.")
    cast(Any, revoke_permissions).short_description = "Revoke selected permissions from users"

    def promote_staff(self, request, queryset):
        if not self._ensure_requester_is_superuser(request):
            messages.error(request, "Only superusers can promote users to staff.")
            return
        updated = queryset.update(is_staff=True)
        messages.success(request, f"Promoted {updated} user(s) to staff.")
    cast(Any, promote_staff).short_description = "Promote selected users to staff"

    def demote_staff(self, request, queryset):
        if not self._ensure_requester_is_superuser(request):
            messages.error(request, "Only superusers can demote staff users.")
            return
        updated = queryset.update(is_staff=False)
        messages.success(request, f"Demoted {updated} user(s) from staff.")
    cast(Any, demote_staff).short_description = "Demote selected staff users"

    def delete_users(self, request, queryset):
        # Prevent non-superusers from deleting superusers
        if not request.user.is_superuser:
            if queryset.filter(is_superuser=True).exists():
                messages.error(request, "You cannot delete superuser accounts unless you are superuser.")
                return
        deleted_count = 0
        for user in queryset:
            # avoid deleting the requesting user accidentally
            if user == request.user:
                messages.warning(request, "Skipped deleting the user performing the action.")
                continue
            user.delete()
            deleted_count += 1
        messages.success(request, f"Deleted {deleted_count} user(s).")
    cast(Any, delete_users).short_description = "Delete selected users"
