from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Book
from .serializers import BookSerializer
from .validators import normalize_isbn, validate_isbn


class ISBNValidationTests(TestCase):
    def test_normalizes_and_accepts_valid_isbn_13(self):
        raw_isbn = '978-0-306-40615-7'

        validate_isbn(raw_isbn)

        self.assertEqual(normalize_isbn(raw_isbn), '9780306406157')

    def test_accepts_isbn_10_with_x_check_digit(self):
        validate_isbn('0-8044-2957-X')

    def test_rejects_invalid_check_digit(self):
        with self.assertRaisesMessage(ValidationError, 'check digit'):
            validate_isbn('978-0-306-40615-8')


class BookModelTests(TestCase):
    def test_creation_sets_timestamps_and_empty_selling_price(self):
        book = Book.objects.create(
            title='A Book',
            author='An Author',
            isbn='0306406152',
            cost_usd=Decimal('12.50'),
            stock_quantity=0,
            category='Fiction',
            supplier_country='US',
        )

        self.assertIsNone(book.selling_price_local)
        self.assertIsNotNone(book.created_at)
        self.assertIsNotNone(book.updated_at)

    def test_clean_normalizes_isbn(self):
        book = Book(
            title='A Book',
            author='An Author',
            isbn='0-306-40615-2',
            cost_usd=Decimal('12.50'),
            stock_quantity=0,
            category='Fiction',
            supplier_country='US',
        )

        book.full_clean()

        self.assertEqual(book.isbn, '0306406152')

    def test_database_rejects_duplicate_normalized_isbn(self):
        Book.objects.create(
            title='First',
            author='An Author',
            isbn='0306406152',
            cost_usd=Decimal('12.50'),
            stock_quantity=1,
            category='Fiction',
            supplier_country='US',
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Book.objects.create(
                title='Second',
                author='Another Author',
                isbn='0-306-40615-2',
                cost_usd=Decimal('15.00'),
                stock_quantity=2,
                category='Fiction',
                supplier_country='US',
            )

    def test_database_rejects_nonpositive_cost(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Book.objects.create(
                title='Invalid',
                author='An Author',
                isbn='0306406152',
                cost_usd=Decimal('0.00'),
                stock_quantity=1,
                category='Fiction',
                supplier_country='US',
            )

    def test_database_rejects_negative_stock(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Book.objects.create(
                title='Invalid',
                author='An Author',
                isbn='0306406152',
                cost_usd=Decimal('12.50'),
                stock_quantity=-1,
                category='Fiction',
                supplier_country='US',
            )


class BookSerializerTests(TestCase):
    def test_normalizes_isbn_and_keeps_server_fields_read_only(self):
        serializer = BookSerializer(
            data={
                'title': 'A Book',
                'author': 'An Author',
                'isbn': '978-0-306-40615-7',
                'cost_usd': '12.50',
                'stock_quantity': 5,
                'category': 'Fiction',
                'supplier_country': 'US',
                'selling_price_local': '1.00',
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['isbn'], '9780306406157')
        self.assertNotIn('selling_price_local', serializer.validated_data)
        serializer.save()
        self.assertEqual(serializer.data['isbn'], '9780306406157')
        self.assertIsNone(serializer.data['selling_price_local'])
        self.assertIsNotNone(serializer.data['created_at'])
        self.assertIsNotNone(serializer.data['updated_at'])

    def test_rejects_invalid_isbn(self):
        serializer = BookSerializer(
            data={
                'title': 'A Book',
                'author': 'An Author',
                'isbn': '978-0-306-40615-8',
                'cost_usd': '12.50',
                'stock_quantity': 5,
                'category': 'Fiction',
                'supplier_country': 'US',
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('isbn', serializer.errors)

    def test_rejects_duplicate_isbn_after_normalization(self):
        Book.objects.create(
            title='Existing',
            author='An Author',
            isbn='9780306406157',
            cost_usd=Decimal('12.50'),
            stock_quantity=1,
            category='Fiction',
            supplier_country='US',
        )
        serializer = BookSerializer(
            data={
                'title': 'Duplicate',
                'author': 'Another Author',
                'isbn': '978-0-306-40615-7',
                'cost_usd': '15.00',
                'stock_quantity': 2,
                'category': 'Fiction',
                'supplier_country': 'US',
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('isbn', serializer.errors)

# Create your tests here.
