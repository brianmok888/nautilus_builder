from __future__ import annotations

from packages.adapter_registry.service import AdapterRegistryService
from packages.instrument_registry.service import InstrumentRegistryService
from services.api.router import ApiResponse


def adapters_payload() -> list[dict[str, object]]:
    return [profile.model_dump(mode="json") for profile in AdapterRegistryService().list_enabled_adapters()]


def instruments_payload(adapter_id: str, query: str) -> ApiResponse:
    try:
        instruments = InstrumentRegistryService().search_instruments(adapter_id=adapter_id, query=query)
    except ValueError as exc:
        return ApiResponse({"error": str(exc)}, status_code=404)
    return ApiResponse([instrument.model_dump(mode="json") for instrument in instruments])


def data_availability_payload(adapter_id: str, instrument_id: str) -> ApiResponse:
    try:
        instrument = InstrumentRegistryService().data_availability(adapter_id=adapter_id, instrument_id=instrument_id)
    except ValueError as exc:
        return ApiResponse({"error": str(exc)}, status_code=404)
    return ApiResponse(instrument.model_dump(mode="json"))
