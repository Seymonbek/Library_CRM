from django.contrib import admin
from unfold.admin import ModelAdmin ,TabularInline
from .models import Category, Publisher, Author, Books, BookCopies

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "parent_category_id", "created_at"]
    search_fields = ["name"]

@admin.register(Publisher)
class PublisherAdmin(ModelAdmin):
    list_display = ["name", "phone_number", "created_at"]
    search_fields = ["name"]

@admin.register(Author)
class AuthorAdmin(ModelAdmin):
    list_display = ["first_name", "last_name", "birth_date"]
    search_fields = ["first_name", "last_name"]

class BookCopyInline(TabularInline): # Kitob ichida nusxalarni ko'rish uchun
    model = BookCopies
    extra = 1 # Avtomatik 1 ta bo'sh qator chiqaradi

@admin.register(Books)
class BooksAdmin(ModelAdmin):
    list_display = ["title", "author", "category", "language", "isbn"]
    list_filter = ["language", "category"]
    search_fields = ["title", "isbn", "author__first_name", "author__last_name"]
    inlines = [BookCopyInline] # Kitoblarni ichida nusxalarini ham qo'shsa bo'ladi

@admin.register(BookCopies)
class BookCopiesAdmin(ModelAdmin):
    list_display = ["inventory_number", "book", "condition", "status"]
    list_filter = ["condition", "status"]
    search_fields = ["inventory_number", "book__title"]