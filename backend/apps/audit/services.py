from .models import AuditLog



class AuditService:


    @staticmethod
    def log(
        user,
        action,
        model_name,
        object_id=None,
        description="",
        ip_address=None
    ):


        return AuditLog.objects.create(

            user=user,

            action=action,

            model_name=model_name,

            object_id=object_id,

            description=description,

            ip_address=ip_address

        )