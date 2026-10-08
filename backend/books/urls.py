from django.urls import path

from .views import (
    BookCategorySearchView,
    BookCalculatePriceView,
    BookDetailView,
    BookListCreateView,
    BookLowStockView,
    health_check,
)

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('books', BookListCreateView.as_view(), name='book-list'),
    path('books/search', BookCategorySearchView.as_view(), name='book-search'),
    path('books/low-stock', BookLowStockView.as_view(), name='book-low-stock'),
    path(
        'books/<int:pk>/calculate-price',
        BookCalculatePriceView.as_view(),
        name='book-calculate-price',
    ),
    path('books/<int:pk>', BookDetailView.as_view(), name='book-detail'),
]
