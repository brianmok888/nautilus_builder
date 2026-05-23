import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MarketProfilePanel } from "./MarketProfilePanel";

const adapters = [
  { adapter_id: "BINANCE_PERP", name: "Binance Perp", venue: "BINANCE" },
  { adapter_id: "DATABENTO_US_EQUITY", name: "Databento US Equity", venue: "XNAS" },
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
        return Response.json([{ adapter_id: "BINANCE_PERP", instrument_id: "BTCUSDT-PERP", symbol: "BTCUSDT-PERP" }]);
      }
      if (url.includes("/api/data-availability/BINANCE_PERP/BTCUSDT-PERP")) {
        return Response.json({
          adapter_id: "BINANCE_PERP",
          instrument_id: "BTCUSDT-PERP",
          supported_timeframes: ["1m", "5m"],
          available_date_ranges: [{ start: "2024-01-01", end: "2024-01-31" }],
        });
      }
      if (url === "/api/backtest-profiles/validate") {
        expect(init?.method).toBe("POST");
        expect(JSON.parse(String(init?.body))).toMatchObject({
          adapter_id: "BINANCE_PERP",
          instrument_id: "BTCUSDT-PERP",
          timeframe: "1m",
        });
        return Response.json({ valid: true, adapter_profile_id: "profile_BINANCE_PERP_BTCUSDT-PERP_1m" });
      }
      return Response.json({ error: url }, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<MarketProfilePanel />);

    expect(await screen.findByText("Binance Perp")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("instrument search"), { target: { value: "BTC" } });
    fireEvent.click(screen.getByRole("button", { name: "Search instruments" }));

    fireEvent.click(await screen.findByRole("button", { name: "Select BTCUSDT-PERP" }));
    expect(await screen.findByText(/Timeframes: 1m, 5m/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("timeframe"), { target: { value: "1m" } });
    fireEvent.change(screen.getByLabelText("start date"), { target: { value: "2024-01-01" } });
    fireEvent.change(screen.getByLabelText("end date"), { target: { value: "2024-01-31" } });
    fireEvent.click(screen.getByRole("button", { name: "Validate profile" }));

    await waitFor(() => expect(screen.getByText("Validated profile: profile_BINANCE_PERP_BTCUSDT-PERP_1m")).toBeInTheDocument());
  });
});
