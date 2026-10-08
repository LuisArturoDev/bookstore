from decimal import Decimal

from django.core.validators import FileExtensionValidator, MinValueValidator, RegexValidator
from django.db import models, transaction

from .validators import normalize_isbn, validate_book_image, validate_isbn


class ISBNField(models.CharField):
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return normalize_isbn(value) if value is not None else None


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = ISBNField(max_length=25, unique=True, validators=[validate_isbn])
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    selling_price_local = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    stock_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    category = models.CharField(max_length=100)
    supplier_country = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2}$',
                message='Enter a two-letter uppercase ISO 3166-1 country code.',
            )
        ],
    )
    image = models.ImageField(
        upload_to='books/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_book_image,
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cost_usd__gt=0),
                name='book_cost_usd_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(stock_quantity__gte=0),
                name='book_stock_quantity_nonnegative',
            ),
        ]

    def clean(self):
        super().clean()
        if self.isbn:
            self.isbn = normalize_isbn(self.isbn)

    def save(self, *args, **kwargs):
        image_name = None
        if self.pk and (
            kwargs.get('update_fields') is None
            or 'image' in kwargs['update_fields']
        ):
            image_name = (
                type(self).objects.filter(pk=self.pk)
                .values_list('image', flat=True)
                .first()
            )

        result = super().save(*args, **kwargs)
        current_image_name = self.image.name if self.image else None
        if image_name and image_name != current_image_name:
            image_storage = self._meta.get_field('image').storage
            transaction.on_commit(
                lambda: image_storage.delete(image_name),
                robust=True,
            )
        return result

    def delete(self, *args, **kwargs):
        image_name = self.image.name if self.image else None
        image_storage = self._meta.get_field('image').storage
        result = super().delete(*args, **kwargs)
        if image_name:
            transaction.on_commit(
                lambda: image_storage.delete(image_name),
                robust=True,
            )
        return result

    def __str__(self):
        return self.title
