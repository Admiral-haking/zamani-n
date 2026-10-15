from .base import IsActiveUser

from .customer import IsCustomer

from .distributor import IsDistributor

from .employee import IsEmployee

from .distributor_customer import IsDistributorCustomerOwner

from .admin import IsAdmin

from .secretary import IsSecretary

from .admin_secretary import IsAdminOrSecretary



__all__ = [

    "IsActiveUser",

    "IsCustomer",

    "IsDistributor",

    "IsEmployee",

    "IsDistributorCustomerOwner",

    "IsAdmin",

    "IsSecretary",

    "IsAdminOrSecretary",

]