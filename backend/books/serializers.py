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
    title = serializers.CharField(max_length=150)
    author = serializers.CharField(max_length=100)
    isbn = ISBNSerializerField(max_length=25)
    category = serializers.CharField(max_length=50)
    remove_image = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('id', 'selling_price_local', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data.pop('remove_image', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        remove_image = validated_data.pop('remove_image', False)
        if remove_image and 'image' not in validated_data:
            instance.image = None
        return super().update(instance, validated_data)
