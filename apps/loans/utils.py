from apps.loans.models import SystemLogs

def perform_logging(serializer, instance, action_type, target_type, details=None):
    """
    Barcha ilovalar (books, loans, users) uchun umumiy log yozish funksiyasi.
    """
    request = serializer.context.get("request")

    if not details:
        details = f"Amal: {action_type.lable}. Obyekt: {str(instance)} (ID: {instance.id})"

    SystemLogs.objects.create(
        admin=request.user if request and request.user.is_authenticated else None,
        action=action_type,
        target=instance.id,
        target_type=target_type,
        details=details
    )