from apps.orders.models import Order


class ReportService:

    @staticmethod
    def total_orders():

        return Order.objects.count()


    @staticmethod
    def total_sales():

        total = 0

        for order in Order.objects.all():

            total += order.total_price

        return total