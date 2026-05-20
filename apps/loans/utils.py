from apps.loans.models import SystemLogs


def _extract_actor(serializer_or_actor = None, explicit_actor = None):
    if explicit_actor is not None:
        if getattr(explicit_actor, "is_authenticated", False):
            return explicit_actor
        return None
    
    if serializer_or_actor is None:
        return None
    
    if hasattr(serializer_or_actor, "context"):
        request = serializer_or_actor.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None
    
    if getattr(serializer_or_actor, "is_authenticated", False):
        return serializer_or_actor

    return None


def perform_logging(serializer_or_actor=None, instance=None, action_type=None, target_type=None, details=None, *, actor=None, target=None,):
    """
    Barcha ilovalar (books, loans, users) uchun umumiy log yozish funksiyasi.
    """

    actor = _extract_actor(serializer_or_actor, actor)

    if action_type is None:
        raise ValueError("action_type majburiy")
    if target_type is None:
        raise ValueError("target_type majburiy")
    
    if target is None and instance is not None:
        target = instance.pk

    if details is None:
        if instance is not None:
            details = f"Amal: {action_type.label}. Obyekt: {instance} (ID: {target})"
        else:
            details = f"Amal: {action_type.label}. Target ID: {target}"

    SystemLogs.objects.create(
        admin=actor,
        action=action_type,
        target=target,
        target_type=target_type,
        details=details
    )