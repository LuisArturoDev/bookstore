from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

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


def make_isbn13(number):
    prefix = f'978{number:09d}'
    checksum = sum(
        int(digit) * (1 if index % 2 == 0 else 3)
        for index, digit in enumerate(prefix)
    )
    return f'{prefix}{(-checksum) % 10}'


def make_book_data(number=1, **overrides):
    data = {
        'title': f'Book {number}',
        'author': 'Test Author',
        'isbn': make_isbn13(number),
        'cost_usd': '12.50',
        'stock_quantity': 5,
        'category': 'Fiction',
        'supplier_country': 'US',
    }
    data.update(overrides)
    return data


class BookCRUDAPITests(APITestCase):
    list_url = '/books'

    def test_create_book_returns_201_and_serialized_book(self):
        response = self.client.post(self.list_url, make_book_data(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['isbn'], make_isbn13(1))
        self.assertIsNone(response.data['selling_price_local'])
        self.assertIn('id', response.data)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
        self.assertEqual(Book.objects.count(), 1)

    def test_create_rejects_invalid_data_with_400(self):
        invalid_inputs = [
            make_book_data(isbn='978-0-306-40615-8'),
            make_book_data(isbn=make_isbn13(2), cost_usd='0.00'),
            make_book_data(isbn=make_isbn13(3), stock_quantity=-1),
            make_book_data(isbn=make_isbn13(4), title=''),
        ]

        for payload in invalid_inputs:
            with self.subTest(payload=payload):
                response = self.client.post(self.list_url, payload, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Book.objects.count(), 0)

    def test_create_rejects_duplicate_normalized_isbn_with_400(self):
        first_isbn = make_isbn13(1)
        self.client.post(
            self.list_url,
            make_book_data(isbn=first_isbn),
            format='json',
        )

        formatted_isbn = '-'.join((first_isbn[:3], first_isbn[3:6], first_isbn[6:12], first_isbn[12:]))
        response = self.client.post(
            self.list_url,
            make_book_data(number=2, isbn=formatted_isbn),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('isbn', response.data)
        self.assertEqual(Book.objects.count(), 1)

    def test_list_returns_paginated_results(self):
        for number in range(1, 13):
            self.client.post(
                self.list_url,
                make_book_data(number),
                format='json',
            )

        first_page = self.client.get(self.list_url)
        second_page = self.client.get(self.list_url, {'page': 2})
        larger_page = self.client.get(self.list_url, {'page_size': 12})

        self.assertEqual(first_page.status_code, status.HTTP_200_OK)
        self.assertEqual(first_page.data['count'], 12)
        self.assertEqual(len(first_page.data['results']), 10)
        self.assertIsNotNone(first_page.data['next'])
        self.assertIsNone(first_page.data['previous'])
        self.assertEqual(len(second_page.data['results']), 2)
        self.assertIsNotNone(second_page.data['previous'])
        self.assertEqual(len(larger_page.data['results']), 12)

    def test_list_returns_empty_page_when_there_are_no_books(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])

    def test_detail_returns_book_and_unknown_id_is_404(self):
        book = Book.objects.create(**make_book_data())

        response = self.client.get(f'{self.list_url}/{book.pk}')
        missing_response = self.client.get(f'{self.list_url}/99999')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], book.pk)
        self.assertEqual(missing_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_replaces_book_fields_and_protects_server_fields(self):
        book = Book.objects.create(**make_book_data())
        updated_data = make_book_data(
            number=2,
            title='Updated title',
            selling_price_local='999.99',
            created_at='2000-01-01T00:00:00Z',
        )

        response = self.client.put(
            f'{self.list_url}/{book.pk}',
            updated_data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated title')
        self.assertEqual(response.data['isbn'], make_isbn13(2))
        self.assertIsNone(response.data['selling_price_local'])
        self.assertNotEqual(response.data['created_at'], '2000-01-01T00:00:00Z')

    def test_put_requires_all_writable_fields_and_invalid_data_is_400(self):
        book = Book.objects.create(**make_book_data())

        incomplete = self.client.put(
            f'{self.list_url}/{book.pk}',
            {'title': 'Incomplete'},
            format='json',
        )
        invalid = self.client.put(
            f'{self.list_url}/{book.pk}',
            make_book_data(number=2, stock_quantity=-3),
            format='json',
        )

        self.assertEqual(incomplete.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_unknown_id_is_404(self):
        response = self.client.put(
            f'{self.list_url}/99999',
            make_book_data(),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_returns_204_and_unknown_id_is_404(self):
        book = Book.objects.create(**make_book_data())

        response = self.client.delete(f'{self.list_url}/{book.pk}')
        missing_response = self.client.delete(f'{self.list_url}/99999')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())
        self.assertEqual(missing_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_is_not_supported(self):
        book = Book.objects.create(**make_book_data())

        response = self.client.patch(
            f'{self.list_url}/{book.pk}',
            {'title': 'Partial update'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
