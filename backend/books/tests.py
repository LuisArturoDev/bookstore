from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from decimal import Decimal
from unittest.mock import Mock, patch

import requests
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Book
from .services.exchange_rate_service import (
    ExchangeRateService,
    ExchangeRateUnavailable,
)
from .services.price_calculation_service import PriceCalculationService
from .serializers import BookSerializer
from .validators import (
    MAX_BOOK_IMAGE_SIZE,
    normalize_isbn,
    validate_book_image,
    validate_isbn,
)


class HealthCheckAPITests(APITestCase):
    def test_health_check_returns_json_for_browser_requests(self):
        browser_accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        response = self.client.get('/health/', HTTP_ACCEPT=browser_accept)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.data, {'status': 'ok'})


class BookImageValidationTests(SimpleTestCase):
    def test_rejects_cover_images_larger_than_five_megabytes(self):
        image = SimpleUploadedFile(
            'cover.png',
            b'x' * (MAX_BOOK_IMAGE_SIZE + 1),
            content_type='image/png',
        )

        with self.assertRaisesMessage(ValidationError, 'must not exceed 5 MB'):
            validate_book_image(image)

    def test_accepts_cover_images_at_the_five_megabyte_limit(self):
        image = SimpleUploadedFile(
            'cover.png',
            b'x' * MAX_BOOK_IMAGE_SIZE,
            content_type='image/png',
        )

        validate_book_image(image)


class ISBNValidationTests(TestCase):
    def test_normalizes_and_accepts_valid_isbn_13(self):
        raw_isbn = '978-0-306-40615-7'

        validate_isbn(raw_isbn)

        self.assertEqual(normalize_isbn(raw_isbn), '9780306406157')

    def test_accepts_isbn_10_with_x_check_digit(self):
        validate_isbn('0-8044-2957-X')

    def test_rejects_invalid_check_digit(self):
        with self.assertRaisesMessage(
            ValidationError,
            'El dígito de control del ISBN-13 no es válido.',
        ):
            validate_isbn('978-0-306-40615-8')

    def test_rejects_isbn_13_without_isbn_prefix(self):
        with self.assertRaisesMessage(
            ValidationError,
            'Un ISBN-13 debe comenzar con 978 o 979.',
        ):
            validate_isbn('232-1-123-65234-0')

    def test_reports_both_prefix_and_check_digit_problems_in_example(self):
        with self.assertRaisesMessage(
            ValidationError,
            'Un ISBN-13 debe comenzar con 978 o 979. '
            'El dígito de control del ISBN-13 no es válido.',
        ):
            validate_isbn('232-1-123-65234-6')

    def test_accepts_valid_isbn_13_with_979_prefix(self):
        validate_isbn('979-10-90636-07-1')


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
        self.assertEqual(
            str(serializer.errors['isbn'][0]),
            'El dígito de control del ISBN-13 no es válido.',
        )

    def test_reports_prefix_and_check_digit_errors_for_invalid_isbn_13(self):
        serializer = BookSerializer(
            data=make_book_data(isbn='232-1-123-65234-6')
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['isbn'][0]),
            'Un ISBN-13 debe comenzar con 978 o 979. '
            'El dígito de control del ISBN-13 no es válido.',
        )

    def test_rejects_title_author_and_category_above_form_limits(self):
        for field, limit in (('title', 150), ('author', 100), ('category', 50)):
            with self.subTest(field=field):
                serializer = BookSerializer(
                    data=make_book_data(**{field: 'x' * (limit + 1)})
                )

                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

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

    def test_rejects_invalid_country_code_and_excess_cost_precision(self):
        invalid_country = BookSerializer(
            data=make_book_data(supplier_country='usa')
        )
        excess_precision = BookSerializer(
            data=make_book_data(cost_usd='12.501')
        )

        self.assertFalse(invalid_country.is_valid())
        self.assertIn('supplier_country', invalid_country.errors)
        self.assertFalse(excess_precision.is_valid())
        self.assertIn('cost_usd', excess_precision.errors)


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


def make_test_image_upload(name='cover.png'):
    image_bytes = BytesIO()
    Image.new('RGB', (4, 6), color='forestgreen').save(image_bytes, format='PNG')
    return SimpleUploadedFile(name, image_bytes.getvalue(), content_type='image/png')


class BookCRUDAPITests(APITestCase):
    list_url = '/books'

    def test_create_book_returns_201_and_serialized_book(self):
        response = self.client.post(self.list_url, make_book_data(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['isbn'], make_isbn13(1))
        self.assertIsNone(response.data['selling_price_local'])
        self.assertIsNone(response.data['image'])
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

    def test_create_book_accepts_and_persists_an_optional_cover_image(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                self.list_url,
                {**make_book_data(), 'image': make_test_image_upload()},
                format='multipart',
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('/media/books/cover', response.data['image'])
            book = Book.objects.get()
            self.assertTrue(book.image.storage.exists(book.image.name))
            self.assertTrue(Path(media_root, book.image.name).is_file())

    def test_cover_replacement_removal_and_book_deletion_clean_up_files(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            created = self.client.post(
                self.list_url,
                {**make_book_data(), 'image': make_test_image_upload()},
                format='multipart',
            )
            book = Book.objects.get(pk=created.data['id'])
            original_image = book.image.name

            with self.captureOnCommitCallbacks(execute=True):
                replaced = self.client.put(
                    f'{self.list_url}/{book.pk}',
                    {**make_book_data(number=2), 'image': make_test_image_upload()},
                    format='multipart',
                )
            book.refresh_from_db()
            replacement_image = book.image.name

            self.assertEqual(replaced.status_code, status.HTTP_200_OK)
            self.assertNotEqual(original_image, replacement_image)
            self.assertFalse(book.image.storage.exists(original_image))
            self.assertTrue(book.image.storage.exists(replacement_image))

            with self.captureOnCommitCallbacks(execute=True):
                removed = self.client.put(
                    f'{self.list_url}/{book.pk}',
                    {**make_book_data(number=2), 'remove_image': 'true'},
                    format='multipart',
                )

            self.assertEqual(removed.status_code, status.HTTP_200_OK)
            self.assertIsNone(removed.data['image'])
            self.assertFalse(book.image.storage.exists(replacement_image))

            with self.captureOnCommitCallbacks(execute=True):
                deleted = self.client.delete(f'{self.list_url}/{book.pk}')

            self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(book.image.storage.exists(replacement_image))

    def test_create_book_rejects_non_image_file_extensions(self):
        response = self.client.post(
            self.list_url,
            {
                **make_book_data(),
                'image': SimpleUploadedFile(
                    'cover.txt',
                    b'not an image',
                    content_type='text/plain',
                ),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)
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
        created_ids = []
        for number in range(1, 13):
            response = self.client.post(
                self.list_url,
                make_book_data(number),
                format='json',
            )
            created_ids.append(response.data['id'])

        first_page = self.client.get(self.list_url)
        second_page = self.client.get(self.list_url, {'page': 2})
        larger_page = self.client.get(self.list_url, {'page_size': 12})

        self.assertEqual(first_page.status_code, status.HTTP_200_OK)
        self.assertEqual(first_page.data['count'], 12)
        self.assertEqual(len(first_page.data['results']), 10)
        self.assertIsNotNone(first_page.data['next'])
        self.assertIsNone(first_page.data['previous'])
        self.assertEqual(
            [book['id'] for book in first_page.data['results']],
            list(reversed(created_ids))[0:10],
        )
        self.assertEqual(len(second_page.data['results']), 2)
        self.assertIsNotNone(second_page.data['previous'])
        self.assertEqual(
            [book['id'] for book in second_page.data['results']],
            list(reversed(created_ids))[10:],
        )
        self.assertEqual(len(larger_page.data['results']), 12)
        self.assertEqual(
            [book['id'] for book in larger_page.data['results']],
            list(reversed(created_ids)),
        )

    def test_list_caps_requested_page_size_at_one_hundred(self):
        Book.objects.bulk_create(
            [
                Book(
                    title=f'Book {number}',
                    author='Test Author',
                    isbn=make_isbn13(number),
                    cost_usd=Decimal('12.50'),
                    stock_quantity=5,
                    category='Fiction',
                    supplier_country='US',
                )
                for number in range(1, 102)
            ]
        )

        response = self.client.get(self.list_url, {'page_size': 101})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 101)
        self.assertEqual(len(response.data['results']), 100)
        self.assertIsNotNone(response.data['next'])

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

    def test_put_rejects_duplicate_normalized_isbn(self):
        existing_book = Book.objects.create(**make_book_data(number=1))
        book_to_update = Book.objects.create(**make_book_data(number=2))

        response = self.client.put(
            f'{self.list_url}/{book_to_update.pk}',
            make_book_data(number=3, isbn=f' {existing_book.isbn[:3]}-{existing_book.isbn[3:]} '),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('isbn', response.data)
        book_to_update.refresh_from_db()
        self.assertEqual(book_to_update.isbn, make_isbn13(2))

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


class BookFilterAPITests(APITestCase):
    category_url = '/books/search'
    low_stock_url = '/books/low-stock'

    def create_book(
        self,
        number,
        *,
        category='Fiction',
        stock_quantity=5,
        title=None,
    ):
        overrides = {
            'category': category,
            'stock_quantity': stock_quantity,
        }
        if title is not None:
            overrides['title'] = title
        return Book.objects.create(
            **make_book_data(number, **overrides)
        )

    def test_category_search_trims_whitespace_and_ignores_case(self):
        matching = self.create_book(1, category='Literature')
        self.create_book(2, category='Science')
        also_matching = self.create_book(3, category='LITERATURE')

        response = self.client.get(
            self.category_url,
            {'category': '  literature  '},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(
            [book['id'] for book in response.data['results']],
            [also_matching.pk, matching.pk],
        )

    def test_search_requires_at_least_one_nonblank_filter(self):
        missing = self.client.get(self.category_url)
        blank = self.client.get(self.category_url, {'category': '   '})
        blank_title = self.client.get(self.category_url, {'title': '   '})

        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('filters', missing.data)
        self.assertEqual(blank.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('filters', blank.data)
        self.assertEqual(blank_title.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('filters', blank_title.data)

    def test_search_matches_title_partially_without_case_sensitivity(self):
        matching = self.create_book(1, title='The Great Gatsby')
        also_matching = self.create_book(
            3,
            category='History',
            title='The Great History',
        )
        self.create_book(2, title='A Different Story')

        response = self.client.get(
            self.category_url,
            {'title': '  gReAt  '},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(
            [book['id'] for book in response.data['results']],
            [also_matching.pk, matching.pk],
        )

    def test_search_combines_title_and_category_filters(self):
        matching = self.create_book(
            1,
            category='Literature',
            title='The Great Gatsby',
        )
        self.create_book(
            2,
            category='Science',
            title='The Great Science Book',
        )
        self.create_book(
            3,
            category='Literature',
            title='A Different Story',
        )

        response = self.client.get(
            self.category_url,
            {'title': 'great', 'category': 'literature'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], matching.pk)

    def test_category_search_returns_empty_page_when_no_books_match(self):
        self.create_book(1, category='Fiction')

        response = self.client.get(
            self.category_url,
            {'category': 'Nonfiction'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])

    def test_category_search_uses_standard_pagination(self):
        for number in range(1, 12):
            self.create_book(number, category='History')

        first_page = self.client.get(
            self.category_url,
            {'category': 'History'},
        )
        second_page = self.client.get(
            self.category_url,
            {'category': 'History', 'page': 2},
        )

        self.assertEqual(first_page.data['count'], 11)
        self.assertEqual(len(first_page.data['results']), 10)
        self.assertIsNotNone(first_page.data['next'])
        self.assertEqual(len(second_page.data['results']), 1)
        self.assertIsNotNone(second_page.data['previous'])


@override_settings(
    EXCHANGE_RATE_API_URL='https://rates.example.test/latest/USD',
    LOCAL_CURRENCY='EUR',
    DEFAULT_EXCHANGE_RATE='0.85',
    EXCHANGE_RATE_TIMEOUT=5,
)
class ExchangeRateServiceTests(SimpleTestCase):
    @patch('books.services.exchange_rate_service.requests.get')
    def test_returns_api_rate_as_decimal_and_uses_configured_currency(self, get):
        response = Mock()
        response.json.return_value = {'rates': {'EUR': 0.92}}
        get.return_value = response

        result = ExchangeRateService().get_rate()

        self.assertEqual(result.rate, Decimal('0.92'))
        self.assertEqual(result.currency, 'EUR')
        self.assertFalse(result.used_fallback)
        get.assert_called_once_with(
            'https://rates.example.test/latest/USD',
            timeout=5,
        )
        response.raise_for_status.assert_called_once_with()

    @patch('books.services.exchange_rate_service.requests.get')
    def test_timeout_uses_configured_fallback(self, get):
        get.side_effect = requests.Timeout('request timed out')

        result = ExchangeRateService().get_rate()

        self.assertEqual(result.rate, Decimal('0.85'))
        self.assertEqual(result.currency, 'EUR')
        self.assertTrue(result.used_fallback)

    @patch('books.services.exchange_rate_service.requests.get')
    def test_connection_error_uses_configured_fallback(self, get):
        get.side_effect = requests.ConnectionError('connection failed')

        result = ExchangeRateService().get_rate()

        self.assertEqual(result.rate, Decimal('0.85'))
        self.assertTrue(result.used_fallback)

    @patch('books.services.exchange_rate_service.requests.get')
    def test_http_error_uses_configured_fallback(self, get):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError('503')
        get.return_value = response

        result = ExchangeRateService().get_rate()

        self.assertEqual(result.rate, Decimal('0.85'))
        self.assertTrue(result.used_fallback)
        response.json.assert_not_called()

    @patch('books.services.exchange_rate_service.requests.get')
    def test_invalid_json_uses_configured_fallback(self, get):
        response = Mock()
        response.json.side_effect = ValueError('invalid JSON')
        get.return_value = response

        result = ExchangeRateService().get_rate()

        self.assertEqual(result.rate, Decimal('0.85'))
        self.assertTrue(result.used_fallback)

    @patch('books.services.exchange_rate_service.requests.get')
    def test_missing_currency_or_invalid_rate_uses_fallback(self, get):
        response = Mock()
        response.json.return_value = {'rates': {'USD': 1, 'EUR': 0}}
        get.return_value = response

        result = ExchangeRateService().get_rate()

        self.assertEqual(result.rate, Decimal('0.85'))
        self.assertTrue(result.used_fallback)

    @patch('books.services.exchange_rate_service.requests.get')
    def test_malformed_payload_values_use_configured_fallback(self, get):
        response = Mock()
        get.return_value = response

        invalid_payloads = [
            [],
            {'rates': []},
            {'rates': {'EUR': 'not-a-number'}},
            {'rates': {'EUR': True}},
            {'rates': {'EUR': 'Infinity'}},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response.json.return_value = payload
                result = ExchangeRateService().get_rate()

                self.assertEqual(result.rate, Decimal('0.85'))
                self.assertTrue(result.used_fallback)

    @override_settings(LOCAL_CURRENCY='EU')
    @patch('books.services.exchange_rate_service.requests.get')
    def test_invalid_currency_configuration_fails_before_http_request(self, get):
        with self.assertRaises(ImproperlyConfigured):
            ExchangeRateService().get_rate()

        get.assert_not_called()

    @override_settings(DEFAULT_EXCHANGE_RATE='NaN')
    @patch('books.services.exchange_rate_service.requests.get')
    def test_invalid_fallback_raises_service_error(self, get):
        get.side_effect = requests.Timeout('request timed out')

        with self.assertRaises(ExchangeRateUnavailable):
            ExchangeRateService().get_rate()


class BookLowStockAPITests(APITestCase):
    low_stock_url = '/books/low-stock'

    def create_book(self, number, *, stock_quantity=5):
        return Book.objects.create(
            **make_book_data(number, stock_quantity=stock_quantity)
        )

    def test_low_stock_uses_inclusive_threshold_and_includes_zero(self):
        zero_stock = self.create_book(1, stock_quantity=0)
        below_threshold = self.create_book(2, stock_quantity=4)
        at_threshold = self.create_book(3, stock_quantity=10)
        self.create_book(4, stock_quantity=11)

        response = self.client.get(self.low_stock_url, {'threshold': '10'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(
            [book['id'] for book in response.data['results']],
            [at_threshold.pk, below_threshold.pk, zero_stock.pk],
        )

    def test_low_stock_defaults_threshold_to_ten(self):
        self.create_book(1, stock_quantity=10)
        self.create_book(2, stock_quantity=11)

        response = self.client.get(self.low_stock_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_low_stock_accepts_zero_threshold(self):
        zero_stock = self.create_book(1, stock_quantity=0)
        self.create_book(2, stock_quantity=1)

        response = self.client.get(self.low_stock_url, {'threshold': '0'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], zero_stock.pk)

    def test_low_stock_rejects_negative_or_noninteger_threshold(self):
        for threshold in ('-1', '1.5', 'abc', '1_0'):
            with self.subTest(threshold=threshold):
                response = self.client.get(
                    self.low_stock_url,
                    {'threshold': threshold},
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('threshold', response.data)

    def test_low_stock_uses_standard_pagination(self):
        for number in range(1, 12):
            self.create_book(number, stock_quantity=1)

        first_page = self.client.get(self.low_stock_url, {'threshold': '1'})
        second_page = self.client.get(
            self.low_stock_url,
            {'threshold': '1', 'page': 2},
        )

        self.assertEqual(first_page.data['count'], 11)
        self.assertEqual(len(first_page.data['results']), 10)
        self.assertIsNotNone(first_page.data['next'])
        self.assertEqual(len(second_page.data['results']), 1)


@override_settings(
    EXCHANGE_RATE_API_URL='https://rates.example.test/latest/USD',
    LOCAL_CURRENCY='EUR',
    DEFAULT_EXCHANGE_RATE='0.85',
    EXCHANGE_RATE_TIMEOUT=5,
)
class PriceCalculationTests(APITestCase):
    def setUp(self):
        self.book = Book.objects.create(
            **make_book_data(cost_usd='15.99', stock_quantity=5)
        )
        self.url = f'/books/{self.book.pk}/calculate-price'

    @patch('books.services.exchange_rate_service.requests.get')
    def test_calculates_persists_and_returns_detailed_price(self, get):
        response_from_api = Mock()
        response_from_api.json.return_value = {'rates': {'EUR': 0.85}}
        get.return_value = response_from_api

        response = self.client.post(self.url, {}, format='json')

        self.book.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['book_id'], self.book.pk)
        self.assertEqual(response.data['cost_usd'], 15.99)
        self.assertEqual(response.data['exchange_rate'], 0.85)
        self.assertEqual(response.data['cost_local'], 13.59)
        self.assertEqual(response.data['margin_percentage'], 40)
        self.assertEqual(response.data['selling_price_local'], 19.03)
        self.assertEqual(response.data['currency'], 'EUR')
        self.assertFalse(response.data['used_fallback'])
        self.assertTrue(response.data['calculation_timestamp'].endswith('Z'))
        self.assertEqual(self.book.selling_price_local, Decimal('19.03'))
        get.assert_called_once()

    @patch('books.services.exchange_rate_service.requests.get')
    def test_uses_and_reports_fallback_when_exchange_api_times_out(self, get):
        get.side_effect = requests.Timeout('request timed out')

        response = self.client.post(self.url, {}, format='json')

        self.book.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['used_fallback'])
        self.assertEqual(response.data['exchange_rate'], 0.85)
        self.assertEqual(self.book.selling_price_local, Decimal('19.03'))

    @override_settings(DEFAULT_EXCHANGE_RATE='NaN')
    @patch('books.services.exchange_rate_service.requests.get')
    def test_returns_503_if_external_rate_and_fallback_are_unavailable(self, get):
        get.side_effect = requests.Timeout('request timed out')

        response = self.client.post(self.url, {}, format='json')

        self.book.refresh_from_db()
        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertEqual(response.data['detail'], 'No valid exchange rate is currently available.')
        self.assertIsNone(self.book.selling_price_local)

    @patch('books.services.exchange_rate_service.requests.get')
    def test_returns_404_for_missing_book_without_calling_external_api(self, get):
        response = self.client.post('/books/99999/calculate-price', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        get.assert_not_called()

    @patch('books.services.exchange_rate_service.requests.get')
    def test_rounds_only_displayed_cost_and_final_price(self, get):
        self.book.cost_usd = Decimal('1.01')
        self.book.save(update_fields=('cost_usd',))

        response_from_api = Mock()
        response_from_api.json.return_value = {'rates': {'EUR': 1.005}}
        get.return_value = response_from_api

        response = self.client.post(self.url, {}, format='json')

        self.book.refresh_from_db()
        self.assertEqual(response.data['cost_local'], 1.02)
        self.assertEqual(response.data['selling_price_local'], 1.42)
        self.assertEqual(self.book.selling_price_local, Decimal('1.42'))

    def test_service_receives_explicit_exchange_rate_service_dependency(self):
        exchange_rate_service = Mock()
        exchange_rate_service.get_rate.return_value = Mock(
            rate=Decimal('0.85'),
            currency='EUR',
            used_fallback=False,
        )
        service = PriceCalculationService(exchange_rate_service)

        calculation = service.calculate(self.book)

        self.assertEqual(calculation.exchange_rate, Decimal('0.85'))
        exchange_rate_service.get_rate.assert_called_once_with()


class DemoBookSeedCommandTests(TestCase):
    def test_seed_adds_200_books_idempotently_and_preserves_existing_records(self):
        existing_book = Book.objects.create(
            title='My existing title',
            author='My existing author',
            isbn='9780140350456',
            cost_usd=Decimal('12.50'),
            stock_quantity=5,
            category='Fiction',
            supplier_country='US',
        )

        call_command('seed_demo_books', stdout=StringIO())
        self.assertEqual(Book.objects.count(), 200)
        existing_book.refresh_from_db()
        self.assertEqual(existing_book.title, 'My existing title')

        call_command('seed_demo_books', stdout=StringIO())
        self.assertEqual(Book.objects.count(), 200)
