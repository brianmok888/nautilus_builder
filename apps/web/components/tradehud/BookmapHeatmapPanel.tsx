"use client";

import { useRef, useEffect, useCallback } from "react";
import type { MarketBookL2, MarketTrade, StrategySignalPreview, GateDecision, ExecutionReport, QuantLevelsContext } from "../../lib/tradehud/types";
import { HeatmapBuffer } from "../../lib/tradehud/heatmap-buffer";
import { HEATMAP_TIME_COLS, HEATMAP_PRICE_ROWS } from "../../lib/tradehud/types";

interface BookmapHeatmapPanelProps {
  bookL2: MarketBookL2 | null;
  trades: MarketTrade[];
  signal: StrategySignalPreview | null;
  gate: GateDecision | null;
  execution: ExecutionReport | null;
  quantLevels: QuantLevelsContext | null;
  stale: boolean;
  missing: boolean;
}

export function BookmapHeatmapPanel({
  bookL2,
  trades,
  signal,
  gate,
  execution,
  quantLevels,
  stale,
  missing,
}: BookmapHeatmapPanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const bufRef = useRef<HeatmapBuffer | null>(null);
  const rafRef = useRef<number>(0);
  const lastAdvanceRef = useRef<number>(0);

  // Initialize buffer on mount
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    bufRef.current = new HeatmapBuffer({
      priceRows: HEATMAP_PRICE_ROWS,
      timeCols: HEATMAP_TIME_COLS,
      priceMin: 104_000,
      priceMax: 106_000,
    });
  }, []);

  // Update buffer with latest book levels
  useEffect(() => {
    const buf = bufRef.current;
    if (!buf || !bookL2) return;

    // Adjust price range if needed
    const allPrices = [...bookL2.bids.map((b) => b.price), ...bookL2.asks.map((a) => a.price)];
    if (allPrices.length === 0) return;
    const minP = Math.min(...allPrices);
    const maxP = Math.max(...allPrices);
    const range = maxP - minP;
    buf.setPriceRange(minP - range * 0.2, maxP + range * 0.2);

    // Advance time column every ~500ms
    const now = Date.now();
    if (now - lastAdvanceRef.current > 400) {
      buf.advanceTime(now * 1_000_000);
      lastAdvanceRef.current = now;

      // Add current book levels to the heatmap
      for (const bid of bookL2.bids) {
        buf.addBidLevel(bid.price, bid.size);
      }
      for (const ask of bookL2.asks) {
        buf.addAskLevel(ask.price, ask.size);
      }
    }
  }, [bookL2]);

  // Canvas render loop
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    const buf = bufRef.current;
    if (!canvas || !buf) {
      rafRef.current = requestAnimationFrame(render);
      return;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      rafRef.current = requestAnimationFrame(render);
      return;
    }

    // Match canvas resolution to display size
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    }

    const w = rect.width;
    const h = rect.height;
    const { priceRows, filledCols, getIntensity } = buf.getRenderData();

    // Clear
    ctx.fillStyle = "#0a0e17";
    ctx.fillRect(0, 0, w, h);

    if (filledCols > 0) {
      const colWidth = w / buf.cfg.timeCols;
      const rowHeight = h / buf.cfg.priceRows;

      // Draw heatmap cells
      const maxIntensity = 50; // normalize
      for (let col = 0; col < filledCols; col++) {
        for (let row = 0; row < priceRows; row++) {
          const { bid, ask } = getIntensity(row, col);
          const total = bid + ask;
          if (total < 0.01) continue;

          const intensity = Math.min(1, total / maxIntensity);
          const x = col * colWidth;
          const y = h - (row + 1) * rowHeight;

          if (ask > bid) {
            // Ask side — red
            ctx.fillStyle = `rgba(248, 113, 113, ${intensity * 0.7})`;
          } else {
            // Bid side — green
            ctx.fillStyle = `rgba(52, 211, 153, ${intensity * 0.7})`;
          }
          ctx.fillRect(x, y, colWidth + 1, rowHeight + 1);
        }
      }

      // Draw mid price line
      const book = bookL2;
      if (book) {
        const mid = (book.bids[0]?.price + book.asks[0]?.price) / 2;
        const { min, max } = buf.currentPriceRange;
        const midY = h - ((mid - min) / (max - min)) * h;
        if (midY >= 0 && midY <= h) {
          ctx.strokeStyle = "rgba(34, 211, 238, 0.6)";
          ctx.lineWidth = 1;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.moveTo(0, midY);
          ctx.lineTo(w, midY);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }

      // Draw quant level lines
      if (quantLevels) {
        const { min, max } = buf.currentPriceRange;
        for (const level of quantLevels.levels) {
          const y = h - ((level.price - min) / (max - min)) * h;
          if (y < 0 || y > h) continue;
          ctx.strokeStyle =
            level.kind === "resistance"
              ? "rgba(248, 113, 113, 0.25)"
              : level.kind === "support"
                ? "rgba(52, 211, 153, 0.25)"
                : "rgba(167, 139, 250, 0.25)";
          ctx.lineWidth = 1;
          ctx.setLineDash([2, 6]);
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(w, y);
          ctx.stroke();
          ctx.setLineDash([]);

          // Label
          ctx.fillStyle = "rgba(200, 211, 224, 0.4)";
          ctx.font = "9px monospace";
          ctx.fillText(level.label, 2, y - 2);
        }
      }

      // Draw trade bubbles (recent)
      const recentTrades = trades.slice(0, 30);
      const { min, max } = buf.currentPriceRange;
      for (let i = 0; i < recentTrades.length; i++) {
        const t = recentTrades[i];
        const x = w - (i / 30) * w;
        const y = h - ((t.price - min) / (max - min)) * h;
        if (y < 0 || y > h) continue;
        const radius = Math.max(1.5, Math.min(6, Math.sqrt(t.notional) / 200));
        ctx.fillStyle = t.side === "buy" ? "rgba(52, 211, 153, 0.6)" : "rgba(248, 113, 113, 0.6)";
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      // Draw signal marker
      if (signal && signal.target_hint) {
        const y = h - ((signal.target_hint - min) / (max - min)) * h;
        if (y >= 0 && y <= h) {
          ctx.fillStyle = "rgba(167, 139, 250, 0.8)";
          ctx.beginPath();
          ctx.moveTo(w - 10, y);
          ctx.lineTo(w - 4, y - 4);
          ctx.lineTo(w - 4, y + 4);
          ctx.fill();
        }
      }

      // Draw execution marker
      if (execution && execution.avg_fill_price) {
        const y = h - ((execution.avg_fill_price - min) / (max - min)) * h;
        if (y >= 0 && y <= h) {
          ctx.strokeStyle = execution.status === "FILLED" ? "#34d399" : "#fbbf24";
          ctx.lineWidth = 1.5;
          ctx.strokeRect(w - 12, y - 3, 8, 6);
        }
      }
    }

    rafRef.current = requestAnimationFrame(render);
  }, [bookL2, trades, signal, execution, quantLevels]);

  useEffect(() => {
    rafRef.current = requestAnimationFrame(render);
    return () => cancelAnimationFrame(rafRef.current);
  }, [render]);

  return (
    <div className="tradehud-panel" style={{ minHeight: 0 }}>
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Bookmap Heatmap</span>
        <span className="tradehud-panel-badge tradehud-panel-badge-info">CANVAS</span>
      </div>
      <div className="tradehud-panel-body-nopad">
        <canvas ref={canvasRef} className="tradehud-heatmap-canvas" />
        {missing && (
          <div className="tradehud-stale-overlay">
            <span className="tradehud-missing-text">MARKET DATA MISSING — NO SOURCE</span>
          </div>
        )}
        {!missing && stale && (
          <div className="tradehud-stale-overlay">
            <span>MARKET DATA STALE</span>
          </div>
        )}
      </div>
    </div>
  );
}
