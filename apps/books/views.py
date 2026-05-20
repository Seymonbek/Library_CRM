from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from drf_spectacular.utils import extend_schema

from apps.users.permissions import ReadOnlyOrLibrarian
from .filters import BookFilter
from .models import Author, BookCopies, Books, Category, Publisher
from .serializers import (
    AuthorSerializer,
    BookCopySerializer,
    BookListSerializer,
    BooksDetailSerializer,
    CategorySerializer,
    PublisherSerializer,
)


class LibrarianManagedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrLibrarian]


@extend_schema(tags=["Books"])
class BookViewSet(LibrarianManagedModelViewSet):
    queryset = Books.objects.all().select_related("author", "category", "publisher")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BookFilter
    search_fields = ["title", "author__first_name", "author__last_name", "isbn"]
    ordering_fields = ["title", "created_at", "page_count"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        return BooksDetailSerializer


@extend_schema(tags=["Authors"])
class AuthorViewSet(LibrarianManagedModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["first_name", "last_name"]
    ordering_fields = ["first_name", "last_name", "created_at"]
    ordering = ["last_name", "first_name"]


@extend_schema(tags=["Book Copies"])
class BookCopyViewSet(LibrarianManagedModelViewSet):
    queryset = BookCopies.objects.all().select_related("book", "book__author")
    serializer_class = BookCopySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "condition", "book"]
    search_fields = ["inventory_number", "book__title"]
    ordering_fields = ["created_at", "inventory_number"]
    ordering = ["-created_at"]


@extend_schema(tags=["Categories"])
class CategoryViewSet(LibrarianManagedModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


@extend_schema(tags=["Publishers"])
class PublisherViewSet(LibrarianManagedModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "phone_number"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]