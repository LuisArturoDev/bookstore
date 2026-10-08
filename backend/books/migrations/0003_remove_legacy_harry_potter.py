from django.db import migrations, transaction


LEGACY_ISBN = '9782123456803'
LEGACY_TITLE = 'Harry Potter - La piedra filosofal'
LEGACY_AUTHOR = 'J. K. Rowling'


def remove_legacy_book(apps, schema_editor):
    Book = apps.get_model('books', 'Book')
    database = schema_editor.connection.alias
    image_storage = Book._meta.get_field('image').storage

    legacy_books = Book.objects.using(database).filter(
        isbn=LEGACY_ISBN,
        title=LEGACY_TITLE,
        author=LEGACY_AUTHOR,
    )

    for book in legacy_books.iterator():
        image_name = book.image.name if book.image else None
        book.delete(using=database)
        if image_name:
            transaction.on_commit(
                lambda name=image_name: image_storage.delete(name),
                using=database,
                robust=True,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_book_image'),
    ]

    operations = [
        migrations.RunPython(
            remove_legacy_book,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
