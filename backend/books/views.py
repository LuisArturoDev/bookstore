from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
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
