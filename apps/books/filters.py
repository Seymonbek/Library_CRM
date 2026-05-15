import django_filters
from .models import Books

class BookFilter(django_filters.FilterSet):
    """
    Kitoblar uchun qidiruv tizimi
    """

    # Kitob nomi ichida qisman qidirish (O'tkan kunlar -> 'o'tkan' deb yozsa ham topadi)
    title = django_filters.CharFilter(lookup_expr='icontains')

    # Ma'lum bir yildan keyin chiqqan kitoblarni qidirish
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr='gte')

    class Meta:
        model = Books
        fields = ['category', 'author', 'language', 'title']
