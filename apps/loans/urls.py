from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import LoanViewSet, FineViewSet

router = SimpleRouter()
router.register(r'loans', LoanViewSet, basename="loan")
router.register(r'fines', FineViewSet, basename="fine")


urlpatterns = router.urls
