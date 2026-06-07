from __future__ import annotations

from typing import TYPE_CHECKING

from packages.adapter_registry.service import AdapterRegistryService
from packages.instrument_registry.service import InstrumentRegistryService
from services.api.router import ApiResponse

if TYPE_CHECKING:
    from packages.postgres.adapter_repository import PostgresAdapterRepository


def adapters_payload(pg_repo: PostgresAdapterRepository | None = None) -> list[dict[str, object]]:
    if pg_repo is not None:
        return [profile.model_dump(mode="json") for profile in pg_repo.list_enabled_adapters()]
    return [profile.model_dump(mode="json") for profile in AdapterRegistryService().list_enabled_adapters()]


def instruments_payload(adapter_id: str, query: str, *, pg_repo: PostgresAdapterRepository | None = None) -> ApiResponse:
    try:
        if pg_repo is not None:
            instruments = pg_repo.search_instruments(adapter_id=adapter_id, query=query)
        else:
            instruments = InstrumentRegistryService().search_instruments(adapter_id=adapter_id, query=query)
    except ValueError as exc:
        return ApiResponse({"error": str(exc)}, status_code=404)
    return ApiResponse([instrument.model_dump(mode="json") for instrument in instruments])


def data_availability_payload(adapter_id: str, instrument_id: str, *, pg_repo: PostgresAdapterRepository | None = None) -> ApiResponse:
    try:
        if pg_repo is not None:
            instrument = pg_repo.data_availability(adapter_id=adapter_id, instrument_id=instrument_id)
        else:
            instrument = InstrumentRegistryService().data_availability(adapter_id=adapter_id, instrument_id=instrument_id)
    except ValueError as exc:
        return ApiResponse({"error": str(exc)}, status_code=404)
    return ApiResponse(instrument.model_dump(mode="json"))


def validate_backtest_profile_payload(payload: dict[str, object]) -> ApiResponse:
    try:
        instrument = InstrumentRegistryService().validate_selection(
            adapter_id=str(payload.get("adapter_id", "")),
            instrument_id=str(payload.get("instrument_id", "")),
            data_type=str(payload.get("data_type", "")),
            timeframe=str(payload.get("timeframe", "")),
            market_type=str(payload.get("market_type", "")),
            date_range=str(payload.get("date_range", "")),
        )
    except ValueError as exc:
        return ApiResponse({"valid": False, "error": str(exc)}, status_code=422)
    return ApiResponse({"valid": True, "instrument": instrument.model_dump(mode="json")})
