import re

from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Book
from .pagination import BookPagination
from .serializers import BookSerializer


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})


class BookListCreateView(ListCreateAPIView):
    queryset = Book.objects.all().order_by('id')
    serializer_class = BookSerializer
    pagination_class = BookPagination
    http_method_names = ['get', 'post', 'head', 'options']


class BookDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    http_method_names = ['get', 'put', 'delete', 'head', 'options']


class BookCategorySearchView(ListAPIView):
    serializer_class = BookSerializer
    pagination_class = BookPagination
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        category = self.request.query_params.get('category', '').strip()
        if not category:
            raise ValidationError(
                {'category': 'This query parameter is required and cannot be blank.'}
            )
        return Book.objects.filter(category__iexact=category).order_by('id')


class BookLowStockView(ListAPIView):
    serializer_class = BookSerializer
    pagination_class = BookPagination
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        raw_threshold = self.request.query_params.get('threshold', '10').strip()
        if not re.fullmatch(r'[0-9]+', raw_threshold):
            raise ValidationError(
                {'threshold': 'Ensure this value is a non-negative integer.'}
            )
        threshold = int(raw_threshold)

        return Book.objects.filter(stock_quantity__lte=threshold).order_by('id')
