from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, AuthorViewSet, BookCopyViewSet, CategoryViewSet, PublisherViewSet

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'book-copies', BookCopyViewSet, basename='copy')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'publishers', PublisherViewSet, basename='publisher')

urlpatterns = router.urls