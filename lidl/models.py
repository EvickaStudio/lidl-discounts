from __future__ import annotations

from datetime import datetime
from unicodedata import category

from pydantic import BaseModel, ConfigDict, Field


class LidlAPIError(RuntimeError):
    pass


class LidlModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Location(LidlModel):
    latitude: float | None = None
    longitude: float | None = None


class Store(LidlModel):
    store_key: str | None = Field(default=None, alias="storeKey")
    name: str | None = None
    address: str | None = None
    postal_code: str | None = Field(default=None, alias="postalCode")
    locality: str | None = None
    distance: float | None = None
    location: Location | None = None

    @property
    def label(self) -> str:
        postcode_and_city = (
            " ".join(value for value in (self.postal_code, self.locality) if value)
            or None
        )
        return ", ".join(
            value for value in (self.name, self.address, postcode_and_city) if value
        )

    @property
    def title(self) -> str:
        if self.name:
            return self.name
        if self.store_key:
            return f"Lidl {self.store_key}"
        return "Lidl"


class Offer(LidlModel):
    id: str | None = None
    title: str | None = None
    brand: str | None = None
    category: str | None = None
    offer_type: str | None = Field(default=None, alias="offerType")
    image_url: str | None = Field(default=None, alias="imageUrl")
    start_validity_date: str | None = Field(default=None, alias="startValidityDate")
    end_validity_date: str | None = Field(default=None, alias="endValidityDate")
    price_box: PriceBox | None = Field(default=None, alias="priceBox")
    packaging: str | None = None
    price_per_unit: str | None = Field(default=None, alias="pricePerUnit")

    @property
    def label(self) -> str:
        return (
            " ".join(value for value in (self.brand, self.title) if value)
            or self.id
            or "-"
        )

    @property
    def period(self) -> str:
        start = _format_date(self.start_validity_date)
        end = _format_date(self.end_validity_date)
        if start and end:
            return f"{start} - {end}"
        return start or end or "-"

    @property
    def price(self) -> str:
        return self.price_box.price if self.price_box else "-"

    @property
    def old_price(self) -> str:
        return self.price_box.old_price if self.price_box else "-"

    @property
    def discount(self) -> str:
        if not self.price_box:
            return "-"
        return _strip_footnote_markers(self.price_box.discount_message)


class PriceBox(LidlModel):
    price_symbol: str | None = Field(default=None, alias="priceSymbol")
    discount_message: str | None = Field(default=None, alias="discountMessage")
    large_part_numeric: float | None = Field(default=None, alias="largePartNumeric")
    large_part_string: str | None = Field(default=None, alias="largePartString")
    small_part_numeric: float | None = Field(default=None, alias="smallPartNumeric")
    small_part_string: str | None = Field(default=None, alias="smallPartString")

    @property
    def price(self) -> str:
        return _format_price(
            self.large_part_numeric, self.large_part_string, self.price_symbol
        )

    @property
    def old_price(self) -> str:
        return _format_price(
            self.small_part_numeric, self.small_part_string, self.price_symbol
        )


class OffersResponse(LidlModel):
    offers: list[Offer] = Field(default_factory=list)
    total_offers: int | None = Field(default=None, alias="totalOffers")


def _format_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        return value[:10] or value


def _format_price(
    numeric: float | None,
    text: str | None,
    symbol: str | None,
) -> str:
    value = text or (
        f"{numeric:.2f}".rstrip("0").rstrip(".") if numeric is not None else None
    )
    if not value:
        return "-"
    if not symbol:
        return value
    return f"{value} {symbol}"


def _strip_footnote_markers(value: str | None) -> str:
    if not value:
        return "-"
    cleaned = "".join(char for char in value if category(char) != "No")
    return cleaned.replace("⁾", "").strip() or "-"
