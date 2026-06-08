from django.db.models import Count, Q
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

    def perform_destroy(self, instance):
        from apps.loans.models import SystemLogs
        from apps.loans.utils import perform_logging

        # Model nomiga qarab action va target_type aniqlash
        model_name = instance.__class__.__name__.lower()
        action_map = {
            'books': (SystemLogs.Action.BOOK_DELETED, SystemLogs.TargetType.BOOK),
            'author': (SystemLogs.Action.AUTHOR_DELETED, SystemLogs.TargetType.AUTHOR),
            'publisher': (SystemLogs.Action.PUBLISHER_DELETED, SystemLogs.TargetType.PUBLISHER),
            'category': (SystemLogs.Action.CATEGORY_DELETED, SystemLogs.TargetType.CATEGORY),
            'bookcopies': (SystemLogs.Action.BOOK_COPY_DELETED, SystemLogs.TargetType.BOOK_COPY),
        }

        action_type, target_type = action_map.get(model_name, (None, None))

        if action_type:
            perform_logging(
                actor=self.request.user,
                instance=instance,
                action_type=action_type,
                target_type=target_type,
                details=f"{instance} o'chirildi"
            )

        instance.delete()



@extend_schema(tags=["Books"])
class BookViewSet(LibrarianManagedModelViewSet):
    queryset = Books.objects.all().select_related("author", "category", "publisher").annotate(
        available_copies_count=Count(
            'bookcopies',
            filter=Q(bookcopies__status='on_shelf')
        )
    )
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