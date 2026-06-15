"use client";

import { useRef, useEffect, useCallback } from "react";
import type {
  MarketBookL2,
  MarketTrade,
  StrategySignalPreview,
  GateDecision,
  ExecutionReport,
  QuantLevelsContext,
} from "../../lib/tradehud/types";
import { HeatmapBuffer } from "../../lib/tradehud/heatmap-buffer";
import {
  HEATMAP_TIME_COLS,
  HEATMAP_PRICE_ROWS,
  MAX_TRADES,
  MAX_SIGNAL_MARKERS,
  MAX_GATE_MARKERS,
  MAX_EXECUTION_MARKERS,
} from "../../lib/tradehud/types";

interface BookmapHeatmapPanelProps {
  bookL2: MarketBookL2 | null;
  trades: MarketTrade[];
  signal: StrategySignalPreview | null;
  gate: GateDecision | null;
  execution: ExecutionReport | null;
  quantLevels: QuantLevelsContext | null;
  stale: boolean;
  missing: boolean;
  sourceStatus: string;
}

/**
 * Dirty-render Bookmap canvas.
 *
 * Canvas only redraws when something changes:
 * - New book/trade data arrives (prop change)
 * - Container resizes (ResizeObserver)
 * - Hover/crosshair
 *
 * NO continuous requestAnimationFrame loop.
 * CPU stays idle when mock/replay state is static.
 */
export function BookmapHeatmapPanel({
  bookL2,
  trades,
  signal,
  gate,
  execution,
  quantLevels,
  stale,
  missing,
  sourceStatus,
}: BookmapHeatmapPanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const bufRef = useRef<HeatmapBuffer | null>(null);
  const rafRef = useRef<number | null>(null);
  const dirtyRef = useRef<boolean>(true);
  const lastAdvanceRef = useRef<number>(0);
  const lastSymbolRef = useRef<string>("");

  // ── scheduleRender: single-RAF guard ──────────────────────────────────────
  const scheduleRender = useCallback((reason: string) => {
    if (rafRef.current !== null) return; // already scheduled
    dirtyRef.current = true;
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;
      doRender();
    });
    // reason logged for debugging; not stored
    void reason;
  }, []);

  // ── Actual canvas render ───────────────────────────────────────────────────
  const doRender = useCallback(() => {
    const canvas = canvasRef.current;
    const buf = bufRef.current;
    if (!canvas || !buf) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Match canvas resolution to display size
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    if (
      canvas.width !== Math.round(rect.width * dpr) ||
      canvas.height !== Math.round(rect.height * dpr)
    ) {
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      ctx.scale(dpr, dpr);
    }

    const w = rect.width;
    const h = rect.height;
    const { priceRows, filledCols, getIntensity } = buf.getRenderData();

    // Clear background
    ctx.fillStyle = "#0a0e17";
    ctx.fillRect(0, 0, w, h);

    if (filledCols > 0) {
      const colWidth = w / buf.cfg.timeCols;
      const rowHeight = h / buf.cfg.priceRows;
      const maxIntensity = 50;

      // Draw heatmap cells
      for (let col = 0; col < filledCols; col++) {
        for (let row = 0; row < priceRows; row++) {
          const { bid, ask } = getIntensity(row, col);
          const total = bid + ask;
          if (total < 0.01) continue;
          const intensity = Math.min(1, total / maxIntensity);
          const x = col * colWidth;
          const y = h - (row + 1) * rowHeight;
          if (ask > bid) {
            ctx.fillStyle = `rgba(248, 113, 113, ${intensity * 0.7})`;
          } else {
            ctx.fillStyle = `rgba(52, 211, 153, ${intensity * 0.7})`;
          }
          ctx.fillRect(x, y, colWidth + 1, rowHeight + 1);
        }
      }

      // Mid price line
      if (bookL2) {
        const mid = (bookL2.bids[0]?.price + bookL2.asks[0]?.price) / 2;
        const { min, max } = buf.currentPriceRange;
        const range = max - min;
        if (range > 0 && isFinite(mid)) {
          const midY = h - ((mid - min) / range) * h;
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
      }

      // Quant level lines
      if (quantLevels) {
        const { min, max } = buf.currentPriceRange;
        const range = max - min;
        if (range > 0) {
          for (const level of quantLevels.levels) {
            const y = h - ((level.price - min) / range) * h;
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
            ctx.fillStyle = "rgba(200, 211, 224, 0.4)";
            ctx.font = "9px monospace";
            ctx.fillText(level.label, 2, y - 2);
          }
        }
      }

      // Trade bubbles (bounded to MAX_TRADES)
      const { min, max } = buf.currentPriceRange;
      const range = max - min;
      if (range > 0) {
        const recentCount = Math.min(30, trades.length);
        for (let i = 0; i < recentCount; i++) {
          const t = trades[i];
          const x = w - (i / 30) * w;
          const y = h - ((t.price - min) / range) * h;
          if (y < 0 || y > h) continue;
          const radius = Math.max(1.5, Math.min(6, Math.sqrt(t.notional) / 200));
          ctx.fillStyle =
            t.side === "buy" ? "rgba(52, 211, 153, 0.6)" : "rgba(248, 113, 113, 0.6)";
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, Math.PI * 2);
          ctx.fill();
        }

        // Signal marker
        if (signal && signal.target_hint) {
          const y = h - ((signal.target_hint - min) / range) * h;
          if (y >= 0 && y <= h) {
            ctx.fillStyle = "rgba(167, 139, 250, 0.8)";
            ctx.beginPath();
            ctx.moveTo(w - 10, y);
            ctx.lineTo(w - 4, y - 4);
            ctx.lineTo(w - 4, y + 4);
            ctx.fill();
          }
        }

        // Execution marker
        if (execution && execution.avg_fill_price) {
          const y = h - ((execution.avg_fill_price - min) / range) * h;
          if (y >= 0 && y <= h) {
            ctx.strokeStyle = execution.status === "FILLED" ? "#34d399" : "#fbbf24";
            ctx.lineWidth = 1.5;
            ctx.strokeRect(w - 12, y - 3, 8, 6);
          }
        }
      }
    }

    dirtyRef.current = false;
  }, [bookL2, trades, signal, execution, quantLevels]);

  // ── Initialize buffer on mount ─────────────────────────────────────────────
  useEffect(() => {
    bufRef.current = new HeatmapBuffer({
      priceRows: HEATMAP_PRICE_ROWS,
      timeCols: HEATMAP_TIME_COLS,
      priceMin: 104_000,
      priceMax: 106_000,
    });
    dirtyRef.current = true;
    scheduleRender("init");
  }, [scheduleRender]);

  // ── Update buffer when book data changes → mark dirty ──────────────────────
  useEffect(() => {
    const buf = bufRef.current;
    if (!buf || !bookL2) return;

    // Adjust price range
    const allPrices = [...bookL2.bids.map((b) => b.price), ...bookL2.asks.map((a) => a.price)];
    if (allPrices.length === 0) return;
    const minP = Math.min(...allPrices);
    const maxP = Math.max(...allPrices);
    const range = maxP - minP;
    buf.setPriceRange(minP - range * 0.2, maxP + range * 0.2);

    // Advance time column every ~400ms
    const now = Date.now();
    if (now - lastAdvanceRef.current > 400) {
      buf.advanceTime(now * 1_000_000);
      lastAdvanceRef.current = now;
      for (const bid of bookL2.bids) {
        buf.addBidLevel(bid.price, bid.size);
      }
      for (const ask of bookL2.asks) {
        buf.addAskLevel(ask.price, ask.size);
      }
    }

    // Symbol change → full dirty + price range reset
    if (bookL2.symbol !== lastSymbolRef.current) {
      lastSymbolRef.current = bookL2.symbol;
    }

    scheduleRender("book-update");
  }, [bookL2, scheduleRender]);

  // ── Redraw when trades/signal/gate/execution change ────────────────────────
  useEffect(() => {
    scheduleRender("trades-or-markers");
  }, [trades, signal, gate, execution, quantLevels, scheduleRender]);

  // ── ResizeObserver: throttled resize → dirty render ────────────────────────
  useEffect(() => {
    const container = containerRef.current;
    if (!container || typeof ResizeObserver === "undefined") return;

    let resizeRaf: number | null = null;
    const ro = new ResizeObserver(() => {
      if (resizeRaf !== null) return;
      resizeRaf = requestAnimationFrame(() => {
        resizeRaf = null;
        scheduleRender("resize");
      });
    });
    ro.observe(container);
    return () => {
      ro.disconnect();
      if (resizeRaf !== null) cancelAnimationFrame(resizeRaf);
    };
  }, [scheduleRender]);

  // ── Cleanup: cancel RAF on unmount ─────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, []);

  // ── Stale/synthetic/missing/unavailable overlay badge ──────────────────────
  const overlayBadge = getOverlayBadge(sourceStatus, missing, stale);

  return (
    <div className="tradehud-panel" style={{ minHeight: 0, display: "flex", flexDirection: "column" }}>
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Bookmap Heatmap</span>
        <span className="tradehud-panel-badge tradehud-panel-badge-info">CANVAS</span>
      </div>
      <div className="tradehud-panel-body-nopad" ref={containerRef} style={{ position: "relative", flex: 1 }}>
        <canvas ref={canvasRef} className="tradehud-heatmap-canvas" />
        {overlayBadge && (
          <div className="tradehud-canvas-overlay-badge">
            <span>{overlayBadge}</span>
          </div>
        )}
      </div>
    </div>
  );
}

/** Determine overlay badge text from source status */
function getOverlayBadge(
  sourceStatus: string,
  missing: boolean,
  stale: boolean,
): string | null {
  if (missing || sourceStatus === "missing") return "MISSING BOOK DATA";
  if (sourceStatus === "unavailable") return "BACKEND UNAVAILABLE — LOCAL MOCK MODE";
  if (sourceStatus === "stale" || stale) return "STALE MARKET DATA";
  if (sourceStatus === "synthetic") return "SYNTHETIC REPLAY";
  return null;
}
