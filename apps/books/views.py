from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from .models import Books, Author, BookCopies, Category, Publisher
from .serializers import BooksDetailSerializer, BookListSerializer, BookCopySerializer, AuthorSerializer, PublisherSerializer, CategorySerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Books'])
class BookViewSet(viewsets.ModelViewSet):
    # N + 1 muammosini yechish uchun select_related
    queryset = Books.objects.all().select_related('author', 'category', 'publisher')

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'language']
    search_fields = ['title', 'author__first_name', 'author__last_name', 'isbn']

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        return BooksDetailSerializer

@extend_schema(tags=['Authors'])
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    search_fields = ['first_name', 'last_name']

@extend_schema(tags=['Book Copies'])
class BookCopyViewSet(viewsets.ModelViewSet):
    queryset = BookCopies.objects.all()
    serializer_class = BookCopySerializer

@extend_schema(tags=['Categories'])
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

@extend_schema(tags=['Publishers'])
class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer