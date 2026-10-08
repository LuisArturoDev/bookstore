from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Book
from .validators import normalize_isbn, validate_isbn


class ISBNSerializerField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault(
            'validators',
            [
                validate_isbn,
                UniqueValidator(queryset=Book.objects.all()),
            ],
        )
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return normalize_isbn(value)


class BookSerializer(serializers.ModelSerializer):
    isbn = ISBNSerializerField(max_length=25)

    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('id', 'selling_price_local', 'created_at', 'updated_at')
