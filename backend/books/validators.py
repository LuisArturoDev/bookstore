import re

from django.core.exceptions import ValidationError


def normalize_isbn(value: str) -> str:
    return re.sub(r'[\s-]', '', value).upper()


def validate_isbn(value: str) -> None:
    isbn = normalize_isbn(value)

    if re.fullmatch(r'\d{9}[\dX]', isbn):
        checksum = sum(
            (10 - index) * (10 if digit == 'X' else int(digit))
            for index, digit in enumerate(isbn)
        )
        if checksum % 11 == 0:
            return
    elif re.fullmatch(r'\d{13}', isbn):
        checksum = sum(
            int(digit) * (1 if index % 2 == 0 else 3)
            for index, digit in enumerate(isbn)
        )
        if checksum % 10 == 0:
            return

    raise ValidationError(
        'Enter a valid ISBN-10 or ISBN-13, including its check digit.',
        code='invalid_isbn',
    )
