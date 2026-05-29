import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { ResultsDashboard } from "./ResultsDashboard";

describe("ResultsDashboard", () => {
  test("renders key metrics from payload", () => {
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

    // Statistic renders title as the metric name
    expect(screen.getByText("total_return")).toBeTruthy();
    expect(screen.getByText("sharpe_ratio")).toBeTruthy();
    // Statistic splits 0.128 into "0" and ".1280" in separate spans
    expect(screen.getByText(".1280")).toBeTruthy();
    // Trades table shows data
    expect(screen.getByText("symbol")).toBeTruthy();
    expect(screen.getByText("BTCUSDT")).toBeTruthy();
    // Fills table shows data
    expect(screen.getByText("fill_id")).toBeTruthy();
    expect(screen.getByText("F-1")).toBeTruthy();
    // Artifacts
    expect(screen.getByText("equity_curve")).toBeTruthy();
  });

  test("renders report summary sections", () => {
    render(
      <ResultsDashboard
        resultId="result-43"
        payload={{
          result_id: "result-43",
          metrics: { trade_count: 1, fill_count: 1 },
          artifacts: { result_json: "artifact://builder/project/user/BacktestResult/result-43" },
          trades: [],
          fills: [],
          logs: [],
          report_summary: {
            sections: ["summary", "equity_curve", "trades", "artifacts"],
            chart_sections: ["equity_curve", "drawdown"],
            metrics: { total_return: 0.05, max_drawdown: -0.045 },
            live_trading_enabled: false,
            execution_authority: false,
          },
        }}
      />,
    );

    expect(screen.getByText("Report Summary")).toBeTruthy();
    expect(screen.getByText(/equity_curve → drawdown/)).toBeTruthy();
  });

  test("keeps dashboard observational without execution authority", () => {
    render(<ResultsDashboard resultId="result-42" />);

    expect(screen.getByText(/observational/i)).toBeTruthy();
    expect(screen.queryByText(/submit order/i)).toBeNull();
    expect(screen.queryByText(/deploy live/i)).toBeNull();
  });
});
