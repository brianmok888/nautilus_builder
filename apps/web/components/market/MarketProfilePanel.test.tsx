import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MarketProfilePanel } from "./MarketProfilePanel";

const adapters = [
  { adapter_id: "BINANCE_PERP", enabled: true, venue: "BINANCE", asset_class: "crypto_perp", data_modes: ["historical_bars"], execution_modes: { backtest: true, paper: false, live: false } },
  { adapter_id: "DATABENTO_US_EQUITY", enabled: true, venue: "DATABENTO", asset_class: "equity", data_modes: ["historical_bars"], execution_modes: { backtest: true, paper: false, live: false } },
];

describe("MarketProfilePanel", () => {
  afterEach(() => vi.restoreAllMocks());

  it("loads adapters, searches instruments, checks availability, and validates a profile", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/adapters") {
        return Response.json(adapters);
      }
      if (url.includes("/api/instruments?")) {
        return Response.json([{ instrument_id: "BTCUSDT-PERP", market_type: "crypto_perp", supported_data_types: ["historical_bars"], supported_timeframes: ["1m", "5m"], available_date_ranges: ["2024-01-01:2024-03-01"] }]);
      }
      if (url.includes("/api/data-availability/BINANCE_PERP/BTCUSDT-PERP")) {
        return Response.json({
          instrument_id: "BTCUSDT-PERP",
          market_type: "crypto_perp",
          supported_data_types: ["historical_bars"],
          supported_timeframes: ["1m", "5m"],
          available_date_ranges: ["2024-01-01:2024-03-01"],
        });
      }
      if (url === "/api/backtest-profiles/validate") {
        expect(init?.method).toBe("POST");
        expect(JSON.parse(String(init?.body))).toMatchObject({
          adapter_id: "BINANCE_PERP",
          instrument_id: "BTCUSDT-PERP",
          data_type: "historical_bars",
          timeframe: "1m",
          market_type: "crypto_perp",
          date_range: "2024-01-01:2024-03-01",
        });
        return Response.json({ valid: true, instrument: { instrument_id: "BTCUSDT-PERP", market_type: "crypto_perp", supported_data_types: ["historical_bars"], supported_timeframes: ["1m"], available_date_ranges: ["2024-01-01:2024-03-01"] } });
      }
      return Response.json({ error: url }, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<MarketProfilePanel />);

    expect(await screen.findByText("BINANCE_PERP — BINANCE")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("instrument search"), { target: { value: "BTC" } });
    fireEvent.click(screen.getByRole("button", { name: "Search instruments" }));

    fireEvent.click(await screen.findByRole("button", { name: "Select BTCUSDT-PERP" }));
    expect(await screen.findByText(/Timeframes: 1m, 5m/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("timeframe"), { target: { value: "1m" } });
    fireEvent.change(screen.getByLabelText("start date"), { target: { value: "2024-01-01" } });
    fireEvent.change(screen.getByLabelText("end date"), { target: { value: "2024-03-01" } });
    fireEvent.click(screen.getByRole("button", { name: "Validate profile" }));

    await waitFor(() => expect(screen.getByText("Validated profile: BTCUSDT-PERP")).toBeInTheDocument());
  });
});
