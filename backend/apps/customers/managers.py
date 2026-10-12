from django.db import models


class CustomerQuerySet(models.QuerySet):

    def active(self):
        return self.filter(
            is_active=True
        )

    def not_deleted(self):
        return self.filter(
            is_deleted=False
        )

    def by_distributor(self, distributor):
        return self.filter(
            distributor=distributor
        )

    def without_distributor(self):
        return self.filter(
            distributor__isnull=True
        )


class CustomerManager(models.Manager):

    def get_queryset(self):
        return CustomerQuerySet(
            self.model,
            using=self._db
        ).not_deleted()

    def active(self):
        return self.get_queryset().active()

    def by_distributor(self, distributor):
        return self.get_queryset().by_distributor(
            distributor
        )

    def without_distributor(self):
        return self.get_queryset().without_distributor()