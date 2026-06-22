import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import type { TradeHudState } from "../../lib/tradehud/types";
import { TradeHudTopBar } from "./TradeHudTopBar";

function stateWithFeedStatus(feedStatus: string): TradeHudState {
  return {
    selectedVenue: "BINANCE",
    selectedSymbol: "BTCUSDT-PERP",
    selectedAccount: "paper",
    mode: "paper",
    bookTop: null,
    bookL2: null,
    trades: [],
    bars: [],
    liquidations: [],
    latestSignalPreview: null,
    latestGateDecision: null,
    latestTradeAction: null,
    latestExecutionReport: null,
    positions: [],
    openOrders: [],
    orderHistory: [],
    tradeHistory: [],
    account: null,
    assets: [],
    quantLevels: null,
    tickToTrade: null,
    runtimeHealth: null,
    backendAvailable: true,
    feedMode: "sse",
    feedStatus,
  };
}

describe("TradeHudTopBar", () => {
  test("labels SSE keepalive/live status as connected, not synthetic", () => {
    render(<TradeHudTopBar state={stateWithFeedStatus("live")} />);

    expect(screen.getByText("SSE CONNECTED")).toBeTruthy();
    expect(screen.queryByText("SSE SYNTHETIC")).toBeNull();
  });
});
