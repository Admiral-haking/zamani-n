from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ProductPriceViewSet



router = DefaultRouter()



router.register(

    r"",

    ProductPriceViewSet,

    basename="prices"

)



urlpatterns = [

    path(

        "",

        include(router.urls)

    )

]