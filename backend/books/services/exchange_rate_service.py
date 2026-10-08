import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class ExchangeRateUnavailable(Exception):
    pass


class InvalidExchangeRateResponse(Exception):
    pass


@dataclass(frozen=True)
class ExchangeRate:
    rate: Decimal
    currency: str
    used_fallback: bool


class ExchangeRateService:
    def get_rate(self) -> ExchangeRate:
        currency = settings.LOCAL_CURRENCY
        if not re.fullmatch(r'[A-Z]{3}', currency):
            raise ImproperlyConfigured(
                'LOCAL_CURRENCY must be a three-letter uppercase currency code.'
            )
        if not settings.EXCHANGE_RATE_API_URL:
            raise ImproperlyConfigured('EXCHANGE_RATE_API_URL must not be empty.')

        try:
            rate = self._fetch_rate(currency)
        except (
            requests.RequestException,
            ValueError,
            InvalidExchangeRateResponse,
        ) as error:
            logger.warning(
                'Exchange-rate request failed (%s); attempting configured fallback.',
                type(error).__name__,
            )
            return ExchangeRate(
                rate=self._get_fallback_rate(error),
                currency=currency,
                used_fallback=True,
            )

        return ExchangeRate(rate=rate, currency=currency, used_fallback=False)

    def _fetch_rate(self, currency: str) -> Decimal:
        response = requests.get(
            settings.EXCHANGE_RATE_API_URL,
            timeout=settings.EXCHANGE_RATE_TIMEOUT,
        )
        response.raise_for_status()

        try:
            payload = response.json()
        except ValueError as error:
            raise InvalidExchangeRateResponse(
                'Exchange-rate API returned invalid JSON.'
            ) from error

        if not isinstance(payload, dict):
            raise InvalidExchangeRateResponse(
                'Exchange-rate API response must be a JSON object.'
            )

        rates = payload.get('rates')
        if not isinstance(rates, dict) or currency not in rates:
            raise InvalidExchangeRateResponse(
                f'Exchange-rate API response does not contain {currency}.'
            )

        raw_rate = rates[currency]
        if isinstance(raw_rate, bool):
            raise InvalidExchangeRateResponse(
                'Exchange-rate API returned a non-numeric rate.'
            )

        try:
            rate = Decimal(str(raw_rate))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise InvalidExchangeRateResponse(
                'Exchange-rate API returned a non-numeric rate.'
            ) from error

        if not rate.is_finite() or rate <= 0:
            raise InvalidExchangeRateResponse(
                'Exchange-rate API rate must be a positive finite number.'
            )

        return rate

    @staticmethod
    def _get_fallback_rate(cause: Exception) -> Decimal:
        try:
            rate = Decimal(str(settings.DEFAULT_EXCHANGE_RATE))
        except (InvalidOperation, TypeError, ValueError) as error:
            logger.error('Configured fallback exchange rate is not numeric.')
            raise ExchangeRateUnavailable(
                'Exchange-rate API failed and configured fallback is invalid.'
            ) from error

        if not rate.is_finite() or rate <= 0:
            logger.error('Configured fallback exchange rate must be positive and finite.')
            raise ExchangeRateUnavailable(
                'Exchange-rate API failed and configured fallback is invalid.'
            ) from cause

        return rate
