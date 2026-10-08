from django.urls import path

from .views import BookDetailView, BookListCreateView, health_check

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('books', BookListCreateView.as_view(), name='book-list'),
    path('books/<int:pk>', BookDetailView.as_view(), name='book-detail'),
]
