import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { ResultsDashboard } from "./ResultsDashboard";

describe("ResultsDashboard", () => {
  test("renders real metrics, trades, fills, logs, and artifacts from payload", () => {
    render(
      <ResultsDashboard
        resultId="result-42"
        payload={{
          result_id: "result-42",
          metrics: { total_return: 0.128, sharpe_ratio: 1.7, max_drawdown: -0.031 },
          artifacts: { equity_curve: "db://artifacts/result-42/equity", report_json: "db://artifacts/result-42/report" },
          trades: [{ trade_id: "T-1", symbol: "BTCUSDT", pnl: 12.5 }],
          fills: [{ fill_id: "F-1", price: 61234.5, quantity: 0.2 }],
          logs: [{ level: "info", message: "backtest completed" }],
        }}
      />,
    );

    expect(screen.getByText("total_return")).toBeTruthy();
    expect(screen.getByText("0.128")).toBeTruthy();
    expect(screen.getByText(/trade_id: T-1/)).toBeTruthy();
    expect(screen.getByText(/fill_id: F-1/)).toBeTruthy();
    expect(screen.getByText(/message: backtest completed/)).toBeTruthy();
    expect(screen.getByText("equity_curve")).toBeTruthy();
    expect(screen.getByText("db://artifacts/result-42/equity")).toBeTruthy();
  });

  test("keeps dashboard observational without execution authority", () => {
    render(<ResultsDashboard resultId="result-42" />);

    expect(screen.getByText(/observational only/i)).toBeTruthy();
    expect(screen.queryByText(/submit order/i)).toBeNull();
    expect(screen.queryByText(/deploy live/i)).toBeNull();
  });
});
