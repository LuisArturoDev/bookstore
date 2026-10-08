import re

from django.core.exceptions import ValidationError


MAX_BOOK_IMAGE_SIZE = 5 * 1024 * 1024


def validate_book_image(image) -> None:
    if image.size > MAX_BOOK_IMAGE_SIZE:
        raise ValidationError(
            'Book cover images must not exceed 5 MB.',
            code='image_too_large',
        )


def normalize_isbn(value: str) -> str:
    return re.sub(r'[\s-]', '', value).upper()


def validate_isbn(value: str) -> None:
    isbn = normalize_isbn(value)

    if re.fullmatch(r'\d{9}[\dX]', isbn):
        checksum = sum(
            (10 - index) * (10 if digit == 'X' else int(digit))
            for index, digit in enumerate(isbn)
        )
        if checksum % 11 != 0:
            raise ValidationError(
                'El dígito de control del ISBN-10 no es válido.',
                code='invalid_isbn_checksum',
            )
        return

    if re.fullmatch(r'\d{13}', isbn):
        errors = []
        if not isbn.startswith(('978', '979')):
            errors.append('Un ISBN-13 debe comenzar con 978 o 979.')
        checksum = sum(
            int(digit) * (1 if index % 2 == 0 else 3)
            for index, digit in enumerate(isbn)
        )
        if checksum % 10 != 0:
            errors.append('El dígito de control del ISBN-13 no es válido.')
        if errors:
            raise ValidationError(' '.join(errors), code='invalid_isbn')
        return

    raise ValidationError(
        'Introduce un ISBN-10 de 10 dígitos o un ISBN-13 de 13 dígitos.',
        code='invalid_isbn',
    )
