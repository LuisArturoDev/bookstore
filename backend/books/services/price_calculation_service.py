from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from ..models import Book

from .exchange_rate_service import ExchangeRateService

MARGIN_PERCENTAGE = Decimal('40')
MONEY_QUANTUM = Decimal('0.01')


def round_money(amount: Decimal) -> Decimal:
    return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PriceCalculation:
    book_id: int
    cost_usd: Decimal
    exchange_rate: Decimal
    cost_local: Decimal
    margin_percentage: Decimal
    selling_price_local: Decimal
    currency: str
    used_fallback: bool
    calculation_timestamp: str


class PriceCalculationService:
    def __init__(self, exchange_rate_service=None):
        self.exchange_rate_service = exchange_rate_service or ExchangeRateService()

    def calculate(self, book: Book) -> PriceCalculation:
        exchange_rate = self.exchange_rate_service.get_rate()
        cost_usd = Decimal(str(book.cost_usd))
        unrounded_cost_local = cost_usd * exchange_rate.rate
        selling_price = round_money(
            unrounded_cost_local
            * (Decimal('1') + MARGIN_PERCENTAGE / Decimal('100'))
        )

        book.selling_price_local = selling_price
        book.save(update_fields=('selling_price_local', 'updated_at'))

        calculation_time = timezone.now()
        return PriceCalculation(
            book_id=book.pk,
            cost_usd=cost_usd,
            exchange_rate=exchange_rate.rate,
            cost_local=round_money(unrounded_cost_local),
            margin_percentage=MARGIN_PERCENTAGE,
            selling_price_local=selling_price,
            currency=exchange_rate.currency,
            used_fallback=exchange_rate.used_fallback,
            calculation_timestamp=calculation_time.isoformat().replace(
                '+00:00',
                'Z',
            ),
        )
