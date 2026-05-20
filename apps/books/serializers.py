from django.db import transaction
from rest_framework import serializers
from .models import Author, Publisher, Category, Books, BookCopies
from apps.loans.models import SystemLogs
from .utils import perform_logging

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "first_name", "last_name", "birth_date", "bio", "created_at"]
        read_only_fields = ["id", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        author = super().create(validated_data)
        perform_logging(self, author, SystemLogs.Action.AUTHOR_ADDED, SystemLogs.TargetType.AUTHOR)
        return author

    @transaction.atomic
    def update(self, instance, validated_data):
        author = super().update(instance, validated_data)
        perform_logging(self, author, SystemLogs.Action.AUTHOR_UPDATED, SystemLogs.TargetType.AUTHOR)
        return author

class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "address", "phone_number", "created_at"]
        read_only_fields = ["id", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        publisher = super().create(validated_data)
        perform_logging(self, publisher, SystemLogs.Action.PUBLISHER_ADDED, SystemLogs.TargetType.PUBLISHER)
        return publisher

    @transaction.atomic
    def update(self, instance, validated_data):
        publisher = super().update(instance, validated_data)
        perform_logging(self, publisher, SystemLogs.Action.PUBLISHER_UPDATED, SystemLogs.TargetType.PUBLISHER)
        return publisher

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "parent_category_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        category = super().create(validated_data)
        perform_logging(self, category, SystemLogs.Action.CATEGORY_ADDED, SystemLogs.TargetType.CATEGORY)
        return category

    @transaction.atomic
    def update(self, instance, validated_data):
        category = super().update(instance, validated_data)
        perform_logging(self, category, SystemLogs.Action.CATEGORY_UPDATED, SystemLogs.TargetType.CATEGORY)
        return category

class BooksDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    author_id = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), source="author", write_only=True)

    publisher_id = serializers.PrimaryKeyRelatedField(queryset=Publisher.objects.all(), source="publisher", write_only=True, allow_null=True, required=False)

    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source="category", write_only=True, allow_null=True, required=False)

    class Meta:
        model = Books
        fields = [
            "id", "title",
            "author", "author_id",
            "category", "category_id",
            "publisher", "publisher_id",
            "isbn", "language",
            "page_count", "description",
            "cover_image", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        book = super().create(validated_data)
        perform_logging(self, book, SystemLogs.Action.BOOK_ADDED, SystemLogs.TargetType.BOOK)
        return book

    @transaction.atomic
    def update(self, instance, validated_data):
        book = super().update(instance,validated_data)
        perform_logging(self, book, SystemLogs.Action.BOOK_UPDATED, SystemLogs.TargetType.BOOK)
        return book

class BookListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Books
        fields = ["id", "title", "author_name", "language", "isbn"]


    def get_author_name(self, obj) -> str:
        return f"{obj.author.first_name} {obj.author.last_name}"


class BookCopySerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(queryset=Books.objects.all(), source="book", write_only=True)

    class Meta:
        model = BookCopies
        fields = ['id', 'book', 'book_id', 'inventory_number', 'condition', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']

    @transaction.atomic
    def create(self, validated_data):
        copy = super().create(validated_data)
        perform_logging(self, copy, SystemLogs.Action.BOOK_COPY_ADDED, SystemLogs.TargetType.BOOK_COPY)
        return copy

    @transaction.atomic
    def update(self, instance, validate_data):
        copy = super().update(instance, validate_data)
        perform_logging(self, copy, SystemLogs.Action.BOOK_COPY_UPDATED, SystemLogs.TargetType.BOOK_COPY)
        return copy