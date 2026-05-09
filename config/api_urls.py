from django.urls import path, include

urlpatterns = [
    # Auth (JWT)
    path("auth/", include("apps.users.urls")),

    # Books & Authors
    path("books/", include("apps.books.urls")),

    # Loans (Ijara)
    path("loans/", include("apps.loans.urls")),
]
