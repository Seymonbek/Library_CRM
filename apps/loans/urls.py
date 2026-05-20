from rest_framework.routers import SimpleRouter

from .views import FineViewSet, LoanViewSet, WaitlistViewSet

router = SimpleRouter()
router.register(r"loans", LoanViewSet, basename="loan")
router.register(r"fines", FineViewSet, basename="fine")
router.register(r"waitlists", WaitlistViewSet, basename="waitlist")

urlpatterns = router.urls