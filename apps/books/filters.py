# import django_filters
# from .models import Book
#
#
# class BookFilter(django_filters.FilterSet):
#     """
#     Kitoblarni filtrlash
#     Ishlatish: /api/v1/books/?author=Qodiriy&genre=Roman
#     """
#     author = django_filters.CharFilter(
#         field_name="author__last_name",
#         lookup_expr="icontains",
#         label="Muallif familiyasi",
#     )
#     genre = django_filters.CharFilter(
#         field_name="genre__name",
#         lookup_expr="icontains",
#         label="Janr nomi",
#     )
#     available = django_filters.BooleanFilter(
#         method="filter_available",
#         label="Faqat mavjudlar",
#     )
#
#     def filter_available(self, queryset, name, value):
#         if value:
#             return queryset.filter(available_copies__gt=0)
#         return queryset
#
#     class Meta:
#         model = Book
#         fields = ["author", "genre", "available"]
