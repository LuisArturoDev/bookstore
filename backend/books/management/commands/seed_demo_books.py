import json
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from books.models import Book
from books.validators import validate_isbn


DEMO_BOOKS_PATH = Path(__file__).resolve().parents[2] / 'data' / 'demo_books.json'
CATEGORIES = ('Fiction', 'Fantasy', 'Mystery', 'Science Fiction', 'Young Adult')


class Command(BaseCommand):
    help = 'Add 200 real-book demo records without changing existing books.'

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with DEMO_BOOKS_PATH.open(encoding='utf-8') as catalog_file:
                demo_books = json.load(catalog_file)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(f'Could not read the demo book catalogue: {error}') from error

        if not isinstance(demo_books, list) or len(demo_books) != 200:
            raise CommandError('The demo book catalogue must contain exactly 200 records.')

        existing_isbns = set(
            Book.objects.filter(isbn__in=[book.get('isbn') for book in demo_books])
            .values_list('isbn', flat=True)
        )
        new_books = []

        for index, record in enumerate(demo_books):
            try:
                title = record['title'].strip()
                author = record['author'].strip()
                isbn = record['isbn'].strip()
            except (AttributeError, KeyError) as error:
                raise CommandError('Each demo book must include title, author, and ISBN.') from error

            if not title or not author:
                raise CommandError('Demo book titles and authors cannot be blank.')

            try:
                validate_isbn(isbn)
            except ValidationError as error:
                raise CommandError(f'Invalid ISBN in demo catalogue: {isbn}') from error

            if isbn in existing_isbns:
                continue

            cost = Decimal('6.99') + Decimal(index % 120) / Decimal('10')
            new_books.append(
                Book(
                    title=title,
                    author=author,
                    isbn=isbn,
                    cost_usd=cost,
                    selling_price_local=(cost * Decimal('1.40')).quantize(Decimal('0.01')),
                    stock_quantity=(index * 7) % 31,
                    category=CATEGORIES[index % len(CATEGORIES)],
                    supplier_country='US',
                )
            )
            existing_isbns.add(isbn)

        Book.objects.bulk_create(new_books, batch_size=100)
        self.stdout.write(
            self.style.SUCCESS(
                f'Added {len(new_books)} demo books; '
                f'{len(demo_books) - len(new_books)} existing ISBNs were skipped.'
            )
        )
