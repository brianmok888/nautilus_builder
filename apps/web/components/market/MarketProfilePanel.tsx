"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchAdapters, fetchDataAvailability, fetchInstruments, validateBacktestProfile } from "../../lib/api";
import type { AdapterSummary, BacktestProfileValidation, DataAvailability, InstrumentSummary } from "../../lib/types";

const AdapterSelector = ({
  adapterId,
  adapters,
  onAdapterChange,
}: {
  adapterId: string;
  adapters: AdapterSummary[];
  onAdapterChange: (adapterId: string) => void;
}) => (
  <label>
    Adapter
    <select aria-label="adapter" value={adapterId} onChange={(event) => onAdapterChange(event.target.value)}>
      {adapters.map((adapter) => (
        <option key={adapter.adapter_id} value={adapter.adapter_id}>
          {adapter.adapter_id} — {adapter.venue}
        </option>
      ))}
    </select>
  </label>
);

const InstrumentSearch = ({
  adapterId,
  instruments,
  loading,
  query,
  onQueryChange,
  onSearch,
  onSelectInstrument,
}: {
  adapterId: string;
  instruments: InstrumentSummary[];
  loading: string;
  query: string;
  onQueryChange: (query: string) => void;
  onSearch: () => void;
  onSelectInstrument: (instrumentId: string) => void;
}) => (
  <>
    <label>
      Instrument
      <input aria-label="instrument search" value={query} onChange={(event) => onQueryChange(event.target.value)} />
    </label>
    <button type="button" disabled={!adapterId || loading !== ""} onClick={onSearch}>
      Search instruments
    </button>
    <ul aria-label="instrument results">
      {instruments.map((instrument) => (
        <li key={instrument.instrument_id}>
          {instrument.instrument_id}
          <button type="button" onClick={() => onSelectInstrument(instrument.instrument_id)}>
            Select {instrument.instrument_id}
          </button>
        </li>
      ))}
    </ul>
  </>
);

const DataAvailabilityPanel = ({ availability, instrumentId }: { availability: DataAvailability | null; instrumentId: string }) => {
  if (!availability) {
    return <section aria-label="data availability">Data availability must be confirmed before job creation.</section>;
  }

  return (
    <section aria-label="data availability">
      <p>Selected instrument: {instrumentId}</p>
      <p>Market type: {availability.market_type}</p>
      <p>Data types: {availability.supported_data_types.join(", ")}</p>
      <p>Timeframes: {availability.supported_timeframes.join(", ")}</p>
      <p>Date ranges: {availability.available_date_ranges.join(", ")}</p>
    </section>
  );
};

export const MarketProfilePanel = () => {
  const [adapters, setAdapters] = useState<AdapterSummary[]>([]);
  const [adapterId, setAdapterId] = useState("");
  const [query, setQuery] = useState("BTC");
  const [instruments, setInstruments] = useState<InstrumentSummary[]>([]);
  const [instrumentId, setInstrumentId] = useState("");
  const [availability, setAvailability] = useState<DataAvailability | null>(null);
  const [dataType, setDataType] = useState("historical_bars");
  const [timeframe, setTimeframe] = useState("1m");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-03-01");
  const [validation, setValidation] = useState<BacktestProfileValidation | null>(null);
  const [loading, setLoading] = useState("Loading adapters");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetchAdapters()
      .then((approvedAdapters) => {
        if (!active) return;
        setAdapters(approvedAdapters);
        setAdapterId(approvedAdapters[0]?.adapter_id ?? "");
        setLoading("");
      })
      .catch((requestError: Error) => {
        if (!active) return;
        setError(requestError.message);
        setLoading("");
      });
    return () => {
      active = false;
    };
  }, []);

  async function searchInstruments() {
    setError("");
    setLoading("Searching instruments");
    setValidation(null);
    try {
      const matches = await fetchInstruments(adapterId, query);
      setInstruments(matches);
    } catch (requestError) {
      setError((requestError as Error).message);
    } finally {
      setLoading("");
    }
  }

  async function selectInstrument(nextInstrumentId: string) {
    setError("");
    setLoading("Checking data availability");
    setInstrumentId(nextInstrumentId);
    setValidation(null);
    try {
      const nextAvailability = await fetchDataAvailability(adapterId, nextInstrumentId);
      setAvailability(nextAvailability);
      setDataType(nextAvailability.supported_data_types[0] ?? "historical_bars");
      setTimeframe(nextAvailability.supported_timeframes[0] ?? "1m");
      const [start, end] = (nextAvailability.available_date_ranges[0] ?? "2024-01-01:2024-03-01").split(":");
      setStartDate(start);
      setEndDate(end);
    } catch (requestError) {
      setError((requestError as Error).message);
    } finally {
      setLoading("");
    }
  }

  async function validateProfile() {
    setError("");
    setLoading("Validating profile");
    try {
      setValidation(
        await validateBacktestProfile({
          adapter_id: adapterId,
          instrument_id: instrumentId,
          data_type: dataType,
          timeframe,
          market_type: availability?.market_type ?? "",
          date_range: `${startDate}:${endDate}`,
        }),
      );
    } catch (requestError) {
      setError((requestError as Error).message);
    } finally {
      setLoading("");
    }
  }

  return (
    <section aria-label="market profile">
      <AdapterSelector adapterId={adapterId} adapters={adapters} onAdapterChange={setAdapterId} />
      <InstrumentSearch
        adapterId={adapterId}
        instruments={instruments}
        loading={loading}
        query={query}
        onQueryChange={setQuery}
        onSearch={searchInstruments}
        onSelectInstrument={selectInstrument}
      />

      {loading ? <p role="status">{loading}</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      <DataAvailabilityPanel availability={availability} instrumentId={instrumentId} />

      <label>
        Data type
        <input aria-label="data type" value={dataType} onChange={(event) => setDataType(event.target.value)} />
      </label>
      <label>
        Timeframe
        <input aria-label="timeframe" value={timeframe} onChange={(event) => setTimeframe(event.target.value)} />
      </label>
      <label>
        Start date
        <input aria-label="start date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
      </label>
      <label>
        End date
        <input aria-label="end date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
      </label>
      <button type="button" disabled={!instrumentId || loading !== ""} onClick={validateProfile}>
        Validate profile
      </button>

      {validation?.valid && validation.instrument ? <p>Validated profile: {validation.instrument.instrument_id}</p> : null}
      {validation && !validation.valid ? <p role="alert">{validation.error ?? "Profile validation failed"}</p> : null}
    </section>
  );
};
