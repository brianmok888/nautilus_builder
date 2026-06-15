"use client";

import React, { useEffect, useRef } from "react";
import type { MarketBar } from "../../lib/tradehud/types";
import { fmtPrice } from "../../lib/tradehud/number-format";
import { fmtTime } from "../../lib/tradehud/time-format";

interface PriceChartOverlayProps {
  bars: MarketBar[];
}

/**
 * Thin price strip: draws recent close prices as a connected line on a canvas
 * when 2+ bars are available, otherwise falls back to a small OHLC table of
 * recent bars.
 */
export const PriceChartOverlay: React.FC<PriceChartOverlayProps> = ({ bars }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const sorted = React.useMemo(
    () => [...(bars ?? [])].sort((a, b) => a.ts_event_ns - b.ts_event_ns),
    [bars],
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || sorted.length < 2) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const cssW = canvas.clientWidth || 300;
    const cssH = canvas.clientHeight || 60;
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    const closes = sorted.map((b) => b.close);
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const range = max - min || 1;

    const xStep = cssW / (closes.length - 1);
    const pad = 4;
    const usableH = cssH - pad * 2;

    // line
    ctx.beginPath();
    closes.forEach((c, i) => {
      const x = i * xStep;
      const y = pad + usableH - ((c - min) / range) * usableH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "#22d3ee"; // cyan
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // last point marker
    const last = closes[closes.length - 1];
    const lx = (closes.length - 1) * xStep;
    const ly = pad + usableH - ((last - min) / range) * usableH;
    ctx.beginPath();
    ctx.arc(lx, ly, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = "#22d3ee";
    ctx.fill();
  }, [sorted]);

  if (!sorted || sorted.length === 0) {
    return (
      <section className="tradehud-panel">
        <header className="tradehud-panel-header">
          <span className="tradehud-panel-title">Price</span>
        </header>
        <div className="tradehud-panel-body">
          <div className="tradehud-missing-text">No price data</div>
        </div>
      </section>
    );
  }

  const last = sorted[sorted.length - 1];
  const first = sorted[0];

  return (
    <section className="tradehud-panel">
      <header className="tradehud-panel-header">
        <span className="tradehud-panel-title">Price</span>
        <span className="tradehud-panel-badge tradehud-panel-badge-info">
          {sorted.length} bars
        </span>
      </header>
      <div className="tradehud-panel-body">
        {sorted.length >= 2 ? (
          <>
            <canvas
              ref={canvasRef}
              style={{ width: "100%", height: 60, display: "block" }}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 4,
                fontSize: 11,
              }}
              className="tradehud-muted"
            >
              <span>{fmtTime(first.ts_event_ns)}</span>
              <span className="tradehud-cyan">close {fmtPrice(last.close)}</span>
              <span>{fmtTime(last.ts_event_ns)}</span>
            </div>
          </>
        ) : (
          <table className="tradehud-table">
            <thead>
              <tr>
                <th>Time</th>
                <th className="tradehud-td-right">O</th>
                <th className="tradehud-td-right">H</th>
                <th className="tradehud-td-right">L</th>
                <th className="tradehud-td-right">C</th>
              </tr>
            </thead>
            <tbody>
              {sorted.slice(-12).map((b, i) => (
                <tr key={i}>
                  <td className="tradehud-muted">{fmtTime(b.ts_event_ns)}</td>
                  <td className="tradehud-td-right">{fmtPrice(b.open)}</td>
                  <td className="tradehud-td-right">{fmtPrice(b.high)}</td>
                  <td className="tradehud-td-right">{fmtPrice(b.low)}</td>
                  <td className="tradehud-td-right tradehud-cyan">
                    {fmtPrice(b.close)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
};

export default PriceChartOverlay;
