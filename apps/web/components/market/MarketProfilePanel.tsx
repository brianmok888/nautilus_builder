"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchAdapters, fetchDataAvailability, fetchInstruments, validateBacktestProfile } from "../../lib/api";
import type { AdapterSummary, BacktestProfileValidation, DataAvailability, InstrumentSummary } from "../../lib/types";

export const MarketProfilePanel = () => {
  const [adapters, setAdapters] = useState<AdapterSummary[]>([]);
  const [adapterId, setAdapterId] = useState("");
  const [query, setQuery] = useState("BTC");
  const [instruments, setInstruments] = useState<InstrumentSummary[]>([]);
  const [instrumentId, setInstrumentId] = useState("");
  const [availability, setAvailability] = useState<DataAvailability | null>(null);
  const [timeframe, setTimeframe] = useState("1m");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-01-31");
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

  const selectedTimeframes = useMemo(
    () => availability?.supported_timeframes ?? availability?.available_timeframes ?? [],
    [availability],
  );

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
      setAvailability(await fetchDataAvailability(adapterId, nextInstrumentId));
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
          timeframe,
          start_date: startDate,
          end_date: endDate,
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
      <label>
        Adapter
        <select aria-label="adapter" value={adapterId} onChange={(event) => setAdapterId(event.target.value)}>
          {adapters.map((adapter) => (
            <option key={adapter.adapter_id} value={adapter.adapter_id}>
              {adapter.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Instrument
        <input aria-label="instrument search" value={query} onChange={(event) => setQuery(event.target.value)} />
      </label>
      <button type="button" disabled={!adapterId || loading !== ""} onClick={searchInstruments}>
        Search instruments
      </button>

      {loading ? <p role="status">{loading}</p> : null}
      {error ? <p role="alert">{error}</p> : null}

      <ul aria-label="instrument results">
        {instruments.map((instrument) => (
          <li key={instrument.instrument_id}>
            {instrument.symbol}
            <button type="button" onClick={() => selectInstrument(instrument.instrument_id)}>
              Select {instrument.instrument_id}
            </button>
          </li>
        ))}
      </ul>

      {availability ? (
        <section aria-label="data availability">
          <p>Selected instrument: {instrumentId}</p>
          <p>Timeframes: {selectedTimeframes.join(", ")}</p>
          <p>Date ranges: {(availability.available_date_ranges ?? []).map((range) => `${range.start} to ${range.end}`).join(", ")}</p>
        </section>
      ) : (
        <section aria-label="data availability">Data availability must be confirmed before job creation.</section>
      )}

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

      {validation?.valid && validation.adapter_profile_id ? <p>Validated profile: {validation.adapter_profile_id}</p> : null}
      {validation && !validation.valid ? <p role="alert">{validation.error ?? "Profile validation failed"}</p> : null}
    </section>
  );
};
