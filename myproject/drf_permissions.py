from rest_framework import permissions


class RequireGroupOrPermission(permissions.BasePermission):
    """Permission that allows access when the user belongs to one of the required groups
    or has one of the required permission codenames.

    Supports two modes on the view:
    - view.required_groups (list of group names) and/or view.required_permissions (list of perm strings)
    - view.required_groups_map (dict action_name -> list of group names) and/or
      view.required_permissions_map (dict action_name -> list of perm strings)

    The permission resolves per-action: if a map exists it checks the mapping for the
    current action name (view.action). Otherwise it falls back to the list.

    Usage in a ViewSet:
        class MyViewSet(...):
            permission_classes = [RequireGroupOrPermission]
            # either global lists:
            required_groups = ['managers']
            required_permissions = ['app_label.permission_codename']
            # or per-action maps:
            required_groups_map = {'approve': ['approvers']}
            required_permissions_map = {'approve': ['app_label.can_approve']}

    If neither groups nor permissions are declared for the view/action this permission
    will be non-blocking (returns True) so it composes nicely with other permission classes.
    Superusers bypass the checks.
    """

    def _resolve_for_action(self, view, attr_name):
        """Resolve an attribute which may be either a list or a mapping for actions.

        Returns a list or None.
        """
        action = getattr(view, "action", None)
        mapping = getattr(view, f"{attr_name}_map", None)
        if mapping and action and isinstance(mapping, dict):
            val = mapping.get(action)
            if val:
                return val

        val = getattr(view, attr_name, None)
        return val

    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        user = getattr(request, "user", None)
        groups = self._resolve_for_action(view, "required_groups")
        perms = self._resolve_for_action(view, "required_permissions")

        # If nothing is required by the view/action, don't block (allow other permissions to decide)
        if not groups and not perms:
            return True

        if not user or not getattr(user, "is_authenticated", False):
            return False

        if getattr(user, "is_superuser", False):
            return True

        if groups:
            for g in groups:
                if user.groups.filter(name=g).exists():
                    return True

        if perms:
            # perms can be a list of permission strings "app_label.codename"
            for p in perms:
                if user.has_perm(p):
                    return True

        return False
