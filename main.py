from __future__ import annotations

import argparse
import json
from typing import Any

import httpx
from pydantic import TypeAdapter

from lidl.config import COUNTRY_DEFAULTS, LidlSettings, get_settings
from lidl.models import LidlAPIError, OffersResponse, Store


class LidlPlus:
    def __init__(
        self,
        *,
        settings: LidlSettings | None = None,
        country: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        timeout: float | None = None,
        language: str | None = None,
    ) -> None:
        settings = settings or get_settings()

        self.country = (country or settings.normalized_country).upper()
        defaults = COUNTRY_DEFAULTS.get(self.country, COUNTRY_DEFAULTS["DE"])
        self.language = language or settings.language or defaults["language"]
        self.latitude = (
            latitude
            if latitude is not None
            else settings.latitude
            if settings.latitude is not None
            else defaults["latitude"]
        )
        self.longitude = (
            longitude
            if longitude is not None
            else settings.longitude
            if settings.longitude is not None
            else defaults["longitude"]
        )
        self.stores_base_url = settings.stores_base_url.rstrip("/") + "/"
        self.offers_base_url = settings.offers_base_url.rstrip("/") + "/"

        app_version = settings.app_version
        self._client = httpx.Client(
            timeout=timeout if timeout is not None else settings.timeout,
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "Accept-Language": self.language,
                "User-Agent": f"LidlPlus/{app_version} Android okhttp/4.12.0",
                "X-Client-Version": app_version,
                "X-Client-Platform": "android",
            },
        )

    def __enter__(self) -> LidlPlus:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _get(self, url: str, *, params: dict[str, Any] | None = None) -> Any:
        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            raise LidlAPIError(
                f"GET {url} failed with HTTP {exc.response.status_code}: {body}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LidlAPIError(f"GET {url} failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise LidlAPIError(f"GET {url} did not return valid JSON") from exc

    def stores(self) -> list[Store]:
        data = self._get(f"{self.stores_base_url}v4/{self.country}")
        return TypeAdapter(list[Store]).validate_python(data)

    def search_stores(self, query: str, *, limit: int = 10) -> list[Store]:
        data = self._get(
            f"{self.stores_base_url}v1/autocomplete/{self.country}",
            params={
                "input": query,
                "language": self.language.split("-", 1)[0],
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
        )
        stores = TypeAdapter(list[Store]).validate_python(data)
        if stores:
            return self._rank_stores(query, stores)[:limit]

        return self.search_stores_from_catalog(query, limit=limit)

    def search_stores_from_catalog(self, query: str, *, limit: int = 10) -> list[Store]:
        terms = [term.casefold() for term in query.split() if term.strip()]
        matches: list[Store] = []

        for store in self.stores():
            searchable = " ".join(
                value
                for value in (
                    store.store_key,
                    store.name,
                    store.address,
                    store.postal_code,
                    store.locality,
                )
                if value
            ).casefold()

            if all(term in searchable for term in terms):
                matches.append(store)

        return self._rank_stores(query, matches)[:limit]

    def _rank_stores(self, query: str, stores: list[Store]) -> list[Store]:
        terms = [term.casefold() for term in query.split() if term.strip()]

        def rank(store: Store) -> tuple[int, float]:
            score = 0
            fields = {
                "store_key": store.store_key,
                "name": store.name,
                "locality": store.locality,
                "postal_code": store.postal_code,
                "address": store.address,
            }
            weights = {
                "store_key": 30,
                "name": 25,
                "locality": 25,
                "postal_code": 20,
                "address": 5,
            }

            for field, value in fields.items():
                text = (value or "").casefold()
                for term in terms:
                    if text == term:
                        score += weights[field] * 3
                    elif text.startswith(term):
                        score += weights[field] * 2
                    elif term in text:
                        score += weights[field]

            distance = store.distance if store.distance is not None else float("inf")
            return -score, distance

        return sorted(stores, key=rank)

    def find_store(self, query: str) -> Store:
        matches = self.search_stores(query, limit=1)
        if not matches:
            raise LookupError(f"No Lidl store found for {query!r} in {self.country}.")
        if not matches[0].store_key:
            raise LookupError(f"Matched Lidl store has no storeKey: {matches[0].label}")
        return matches[0]

    def offers(self, store_key: str) -> OffersResponse:
        data = self._get(f"{self.offers_base_url}v4/{self.country}/{store_key}/offers")
        return OffersResponse.model_validate(data)

    def offers_for_store_search(self, query: str) -> tuple[Store, OffersResponse]:
        store = self.find_store(query)
        return store, self.offers(store.store_key or "")


def print_store(store: Store) -> None:
    print(f"{store.title} ({store.store_key or '-'})")
    print(store.label or "-")

    if (
        store.location
        and store.location.latitude is not None
        and store.location.longitude is not None
    ):
        print(f"{store.location.latitude}, {store.location.longitude}")

    if store.distance is not None:
        print(f"Distance: {store.distance:.0f} m")


def _ellipsize(value: str | None, width: int) -> str:
    text = value or "-"
    if len(text) <= width:
        return text
    if width <= 3:
        return "." * width
    return text[: width - 3] + "..."


def _offer_name(brand: str | None, title: str | None, fallback: str | None) -> str:
    if brand and title:
        return f"{brand} - {title}"
    return title or brand or fallback or "-"


def print_offers(response: OffersResponse, *, limit: int | None) -> None:
    total = response.total_offers or len(response.offers)
    offers = response.offers if limit is None else response.offers[:limit]
    print(f"Offers: {total}" if limit is None else f"Offers: {len(offers)} of {total}")

    if not offers:
        return

    print(
        f"  {'Product':<58} | {'Offer':>10} | {'Regular':>10} | "
        f"{'Deal':<8} | {'Unit':<18} | {'Valid'}"
    )
    print(
        f"  {'-' * 58} | {'-' * 10} | {'-' * 10} | {'-' * 8} | {'-' * 18} | {'-' * 23}"
    )

    for offer in offers:
        product = _ellipsize(_offer_name(offer.brand, offer.title, offer.id), 58)
        price = _ellipsize(offer.price, 10)
        old_price = _ellipsize(offer.old_price, 10)
        discount = _ellipsize(offer.discount, 8)
        unit = _ellipsize(offer.price_per_unit, 18)
        period = _ellipsize(offer.period, 23)

        print(
            f"  {product:<58} | "
            f"{price:>10} | {old_price:>10} | "
            f"{discount:<8} | {unit:<18} | {period}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find a Lidl Plus store and print current offers."
    )

    parser.add_argument(
        "query",
        help="Store search query, e.g. Hamburg, Hamm, postcode, or street",
    )
    parser.add_argument(
        "--country",
        default=None,
        help="Country code, default: LIDL_COUNTRY or DE",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of offers to print, default: all",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Accept-Language override, e.g. de-DE or en-GB",
    )
    parser.add_argument(
        "--latitude",
        type=float,
        default=None,
        help="Latitude used for store autocomplete ranking",
    )
    parser.add_argument(
        "--longitude",
        type=float,
        default=None,
        help="Longitude used for store autocomplete ranking",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="HTTP timeout override in seconds",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.limit is not None and args.limit < 1:
        print("Error: --limit must be at least 1")
        return 2

    try:
        with LidlPlus(
            country=args.country,
            latitude=args.latitude,
            longitude=args.longitude,
            timeout=args.timeout,
            language=args.language,
        ) as lidl:
            store, offers = lidl.offers_for_store_search(args.query)

        print_store(store)
        print_offers(offers, limit=args.limit)
        return 0

    except LookupError as exc:
        print(f"Error: {exc}")
        return 1
    except LidlAPIError as exc:
        print(f"API error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
