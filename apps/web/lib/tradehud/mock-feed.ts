/**
 * Deterministic mock data generator for TradeHUD.
 * No Math.random() — uses seeded LCG PRNG for reproducibility.
 *
 * All data is synthetic/mock provenance. Clearly labeled.
 */
import type {
  MarketBookTop,
  MarketBookL2,
  MarketTrade,
  MarketBar,
  LiquidationEvent,
  StrategySignalPreview,
  GateDecision,
  TradeActionEvidence,
  ExecutionReport,
  AccountSnapshot,
  PositionSnapshot,
  OpenOrderSnapshot,
  OrderEvent,
  FillEvent,
  QuantLevelsContext,
  TickToTradeTrace,
  RuntimeHealth,
  LaneHealth,
  AssetSnapshot,
  BookLevel,
  ExecutionStatusType,
} from "./types";
import { MAX_TRADES, MAX_ORDER_EVENTS, MAX_FILLS, MAX_BARS, MAX_LIQUIDATIONS } from "./types";
import { syntheticFreshness } from "./freshness";
import { RingBuffer } from "./ring-buffer";

// ─── Seeded PRNG (Linear Congruential Generator) ──────────────────────────────

export class SeededRng {
  private state: number;
  constructor(seed: number) {
    this.state = seed >>> 0;
  }
  next(): number {
    // LCG constants from Numerical Recipes
    this.state = (1664525 * this.state + 1013904223) >>> 0;
    return this.state / 0x100000000;
  }
  range(min: number, max: number): number {
    return min + this.next() * (max - min);
  }
  int(min: number, max: number): number {
    return Math.floor(this.range(min, max + 1));
  }
  bool(prob = 0.5): boolean {
    return this.next() < prob;
  }
  pick<T>(arr: T[]): T {
    return arr[this.int(0, arr.length - 1)];
  }
}

// ─── Symbol profiles ───────────────────────────────────────────────────────────

interface SymbolProfile {
  symbol: string;
  basePrice: number;
  tickSize: number;
  priceDecimals: number;
  qtyDecimals: number;
}

const SYMBOL_PROFILES: Record<string, SymbolProfile> = {
  "BTCUSDT-PERP": { symbol: "BTCUSDT-PERP", basePrice: 105_000, tickSize: 0.1, priceDecimals: 1, qtyDecimals: 4 },
  "ETHUSDT-PERP": { symbol: "ETHUSDT-PERP", basePrice: 3_800, tickSize: 0.01, priceDecimals: 2, qtyDecimals: 4 },
};

const VENUE = "BINANCE-FUTURES";
const ACCOUNT_ID = "acc_paper_001";

// ─── Deterministic hash stub ───────────────────────────────────────────────────

function hashStub(prefix: string, n: number): string {
  const hex = (n * 2654435761 >>> 0).toString(16).padStart(8, "0");
  return `${prefix}_${hex}${hex}${hex}${hex}`;
}

// ─── Mock state holder ─────────────────────────────────────────────────────────

export class MockFeed {
  private rng: SeededRng;
  private profile: SymbolProfile;
  private currentPrice: number;
  private tickCount = 0;

  readonly trades: RingBuffer<MarketTrade>;
  readonly bars: RingBuffer<MarketBar>;
  readonly liquidations: RingBuffer<LiquidationEvent>;
  readonly orderEvents: RingBuffer<OrderEvent>;
  readonly fillEvents: RingBuffer<FillEvent>;

  constructor(symbol: string = "BTCUSDT-PERP", seed: number = 42) {
    this.rng = new SeededRng(seed);
    this.profile = SYMBOL_PROFILES[symbol] ?? SYMBOL_PROFILES["BTCUSDT-PERP"];
    this.currentPrice = this.profile.basePrice;
    this.trades = new RingBuffer(MAX_TRADES);
    this.bars = new RingBuffer(MAX_BARS);
    this.liquidations = new RingBuffer(MAX_LIQUIDATIONS);
    this.orderEvents = new RingBuffer(MAX_ORDER_EVENTS);
    this.fillEvents = new RingBuffer(MAX_FILLS);
    this.seedHistory();
    this.seedEvidence();
  }

  private nowNs(): number {
    return Date.now() * 1_000_000;
  }

  private seedHistory(): void {
    // Seed 200 trades, 60 bars of history
    const baseTs = this.nowNs();
    for (let i = 200; i > 0; i--) {
      const ts = baseTs - i * 2_000_000_000; // 2s apart
      this.tickCount++;
      this.currentPrice += this.rng.range(-15, 15);
      this.trades.push(this.makeTrade(ts));
    }
    for (let i = 60; i > 0; i--) {
      const ts = baseTs - i * 60_000_000_000; // 1m apart
      this.bars.push(this.makeBar(ts));
    }
  }

  private seedEvidence(): void {
    // Pre-seed one of each gate type and execution evidence
    // These will be retrieved by getEvidenceSnapshot
  }

  private makeTrade(ts: number): MarketTrade {
    const side = this.rng.bool(0.5) ? "buy" : "sell";
    const aggressor = side;
    const qty = this.rng.range(0.01, 5.0);
    const notional = qty * this.currentPrice;
    const isLarge = notional > 500_000;
    const isSweep = this.rng.bool(0.05);
    const isLiq = this.rng.bool(0.03);

    let liqSide: "long_liq" | "short_liq" | null = null;
    if (isLiq) {
      // Binance Futures force-order semantics:
      // SELL force order = LONG_LIQ, BUY force order = SHORT_LIQ
      liqSide = side === "sell" ? "long_liq" : "short_liq";
    }

    const trade: MarketTrade = {
      trade_id: `trd_${this.tickCount}`,
      symbol: this.profile.symbol,
      price: this.currentPrice,
      qty,
      notional,
      side,
      aggressor,
      source: "mock_feed",
      is_large_trade: isLarge,
      is_sweep: isSweep,
      is_liquidation: isLiq,
      liq_side: liqSide,
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
    return trade;
  }

  private makeBar(ts: number): MarketBar {
    const o = this.currentPrice;
    const highOffset = Math.abs(this.rng.range(0, 50));
    const lowOffset = Math.abs(this.rng.range(0, 50));
    this.currentPrice += this.rng.range(-20, 20);
    return {
      symbol: this.profile.symbol,
      open: o,
      high: o + highOffset,
      low: o - lowOffset,
      close: this.currentPrice,
      volume: this.rng.range(10, 500),
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  // ─── Public tick: advance the mock world ─────────────────────────────────────

  tick(): void {
    const ts = this.nowNs();
    this.tickCount++;

    // Price random walk
    const vol = this.profile.basePrice * 0.0008;
    this.currentPrice += this.rng.range(-vol, vol);

    // Emit trades (1-4 per tick)
    const numTrades = this.rng.int(1, 4);
    for (let i = 0; i < numTrades; i++) {
      this.trades.push(this.makeTrade(ts + i));
    }

    // Occasionally emit a bar
    if (this.tickCount % 30 === 0) {
      this.bars.push(this.makeBar(ts));
    }
  }

  // ─── Snapshot getters ───────────────────────────────────────────────────────

  getBookTop(): MarketBookTop {
    const ts = this.nowNs();
    const spread = this.profile.tickSize * this.rng.range(1, 5);
    const bid = this.currentPrice - spread / 2;
    const ask = this.currentPrice + spread / 2;
    const bidSize = this.rng.range(0.5, 20);
    const askSize = this.rng.range(0.5, 20);
    const mid = (bid + ask) / 2;
    return {
      symbol: this.profile.symbol,
      bid_price: bid,
      ask_price: ask,
      bid_size: bidSize,
      ask_size: askSize,
      mid_price: mid,
      spread,
      spread_bps: (spread / mid) * 10_000,
      microprice: mid + (askSize - bidSize) / (askSize + bidSize) * spread * 0.5,
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getBookL2(): MarketBookL2 {
    const ts = this.nowNs();
    const top = this.getBookTop();
    const bids: BookLevel[] = [];
    const asks: BookLevel[] = [];
    let bidTotal = 0;
    let askTotal = 0;
    for (let i = 0; i < 15; i++) {
      const bidPrice = top.bid_price - i * this.profile.tickSize * this.rng.range(1, 5);
      const bidSize = this.rng.range(0.1, 30) * (1 - i * 0.05);
      bidTotal += bidSize;
      bids.push({ price: bidPrice, size: bidSize, total: bidTotal, age_ms: this.rng.int(0, 3000), source: "mock" });

      const askPrice = top.ask_price + i * this.profile.tickSize * this.rng.range(1, 5);
      const askSize = this.rng.range(0.1, 30) * (1 - i * 0.05);
      askTotal += askSize;
      asks.push({ price: askPrice, size: askSize, total: askTotal, age_ms: this.rng.int(0, 3000), source: "mock" });
    }
    const top5Bid = bids.slice(0, 5).reduce((s, l) => s + l.size, 0);
    const top5Ask = asks.slice(0, 5).reduce((s, l) => s + l.size, 0);
    return {
      symbol: this.profile.symbol,
      bids,
      asks,
      spread: top.spread,
      spread_bps: top.spread_bps,
      microprice: top.microprice,
      top5_imbalance: top5Bid / (top5Bid + top5Ask),
      checksum: hashStub("ck", this.tickCount),
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getTrades(): MarketTrade[] {
    return this.trades.toArray().reverse(); // newest first
  }

  getSignalPreview(): StrategySignalPreview {
    const ts = this.nowNs();
    const dir = this.rng.pick(["long", "short", "flat"] as const);
    const conf = this.rng.range(0.3, 0.85);
    return {
      signal_id: `sig_${this.tickCount}`,
      symbol: this.profile.symbol,
      feature_hash: hashStub("feat", this.tickCount),
      context_hash: hashStub("ctx", this.tickCount),
      policy_hash: hashStub("pol", this.tickCount),
      graph_trace_hash: hashStub("gtr", this.tickCount),
      confidence_score: conf,
      direction: dir,
      target_hint: dir === "long" ? this.currentPrice * 1.01 : dir === "short" ? this.currentPrice * 0.99 : null,
      invalidation_hint: dir === "long" ? this.currentPrice * 0.995 : dir === "short" ? this.currentPrice * 1.005 : null,
      size_hint: dir === "flat" ? null : this.rng.range(0.1, 2.0),
      preview_note: "Preview only — NOT EXECUTABLE",
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getGateDecision(cycle: number): GateDecision {
    const ts = this.nowNs();
    // Cycle through: approved, hold, rejected
    const decisions = ["APPROVED", "HOLD", "REJECTED"] as const;
    const decision = decisions[cycle % 3];
    return {
      decision_id: `gate_${this.tickCount}_${cycle}`,
      decision,
      first_blocking_gate: decision === "APPROVED" ? null : this.rng.pick(["risk_limit", "confidence_floor", "regime_filter", "max_position"]),
      reason_code: decision === "APPROVED" ? "all_gates_passed" : this.rng.pick(["GATE_RISK_LIMIT", "GATE_CONFIDENCE_FLOOR", "GATE_REGIME_FILTER"]),
      confidence_delta: this.rng.range(-0.1, 0.15),
      size_modifier: decision === "APPROVED" ? this.rng.range(0.5, 1.0) : 0,
      target_hint: decision === "APPROVED" ? this.currentPrice * 1.005 : null,
      invalidation_hint: decision === "APPROVED" ? this.currentPrice * 0.995 : null,
      gate_decision_hash: hashStub("gd", this.tickCount * 7 + cycle),
      source_signal_hash: hashStub("sig", this.tickCount * 3),
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getTradeActionEvidence(gateHash: string): TradeActionEvidence {
    const ts = this.nowNs();
    return {
      action_id: `ta_${this.tickCount}`,
      action: "PLACE_LIMIT",
      side: this.rng.bool(0.5) ? "buy" : "sell",
      price: this.currentPrice,
      qty: this.rng.range(0.05, 1.0),
      trade_action_hash: hashStub("ta", this.tickCount * 11),
      source_gate_decision_hash: gateHash,
      created_by: "run_gate_engine",
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getExecutionReport(): ExecutionReport {
    const ts = this.nowNs();
    const statuses: ExecutionStatusType[] = ["FILLED", "LIVE", "PARTIAL_FILL", "CANCELED", "REJECTED"];
    const status = this.rng.pick(statuses);
    const submitTs = ts - this.rng.int(100_000, 5_000_000); // ns ago
    const ackTs = status === "REJECTED" ? null : submitTs + this.rng.int(50_000, 500_000);
    const fillTs = (status === "FILLED" || status === "PARTIAL_FILL") ? (ackTs ?? submitTs) + this.rng.int(100_000, 2_000_000) : null;
    return {
      report_id: `exec_${this.tickCount}`,
      status,
      exchange_order_id: status === "REJECTED" ? null : `BIN-${this.rng.int(1e8, 9e8)}`,
      client_order_id: `CO-${this.tickCount}`,
      trade_action_hash: hashStub("ta", this.tickCount * 13),
      symbol: this.profile.symbol,
      side: this.rng.bool(0.5) ? "buy" : "sell",
      filled_qty: status === "FILLED" ? this.rng.range(0.05, 1.0) : status === "PARTIAL_FILL" ? this.rng.range(0.01, 0.3) : 0,
      avg_fill_price: status === "FILLED" || status === "PARTIAL_FILL" ? this.currentPrice : null,
      submit_ts_ns: submitTs,
      ack_ts_ns: ackTs,
      fill_ts_ns: fillTs,
      submit_to_ack_us: ackTs ? (ackTs - submitTs) / 1000 : null,
      ack_to_fill_us: ackTs && fillTs ? (fillTs - ackTs) / 1000 : null,
      rejection_reason: status === "REJECTED" ? "INSUFFICIENT_MARGIN" : null,
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getAccount(): AccountSnapshot {
    const ts = this.nowNs();
    const balance = 250_000;
    const unrealized = this.rng.range(-5_000, 8_000);
    return {
      account_id: ACCOUNT_ID,
      venue: VENUE,
      balance,
      equity: balance + unrealized,
      available_margin: balance * 0.7,
      margin_used: this.rng.range(5_000, 50_000),
      unrealized_pnl: unrealized,
      realized_pnl: this.rng.range(-2_000, 15_000),
      currency: "USDT",
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getPositions(): PositionSnapshot[] {
    const ts = this.nowNs();
    const pos: PositionSnapshot = {
      symbol: this.profile.symbol,
      venue: VENUE,
      side: this.rng.bool(0.5) ? "long" : "short",
      qty: this.rng.range(0.1, 3.0),
      entry_price: this.currentPrice - this.rng.range(-200, 200),
      mark_price: this.currentPrice,
      unrealized_pnl: this.rng.range(-3_000, 5_000),
      realized_pnl: this.rng.range(-500, 2_000),
      margin: this.rng.range(5_000, 30_000),
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
    // Occasionally add ETH position
    if (this.profile.symbol !== "ETHUSDT-PERP") {
      const ethProfile = SYMBOL_PROFILES["ETHUSDT-PERP"];
      return [pos, {
        symbol: "ETHUSDT-PERP",
        venue: VENUE,
        side: this.rng.bool(0.5) ? "long" : "short",
        qty: this.rng.range(1, 20),
        entry_price: ethProfile.basePrice,
        mark_price: ethProfile.basePrice + this.rng.range(-30, 30),
        unrealized_pnl: this.rng.range(-800, 1_200),
        realized_pnl: 0,
        margin: this.rng.range(2_000, 10_000),
        ts_event_ns: ts,
        ...syntheticFreshness(ts),
      }];
    }
    return [pos];
  }

  getOpenOrders(): OpenOrderSnapshot[] {
    const ts = this.nowNs();
    const orders: OpenOrderSnapshot[] = [];
    const count = this.rng.int(0, 4);
    for (let i = 0; i < count; i++) {
      orders.push({
        order_id: `O-${this.tickCount}-${i}`,
        client_order_id: `CO-${this.tickCount}-${i}`,
        symbol: this.profile.symbol,
        venue: VENUE,
        side: this.rng.bool(0.5) ? "buy" : "sell",
        order_type: this.rng.pick(["LIMIT", "STOP", "STOP_LIMIT"]),
        price: this.currentPrice + this.rng.range(-100, 100),
        qty: this.rng.range(0.05, 1.5),
        filled_qty: 0,
        status: "LIVE",
        ts_event_ns: ts,
        ...syntheticFreshness(ts),
      });
    }
    return orders;
  }

  getOrderHistory(): OrderEvent[] {
    return this.orderEvents.toArray().reverse();
  }

  getTradeHistory(): FillEvent[] {
    return this.fillEvents.toArray().reverse();
  }

  getAssets(): AssetSnapshot[] {
    const ts = this.nowNs();
    return [
      { asset: "USDT", free: 250_000, locked: 30_000, usd_value: 250_000, ...syntheticFreshness(ts) },
      { asset: "BTC", free: 0.5, locked: 0.1, usd_value: 52_500, ...syntheticFreshness(ts) },
      { asset: "ETH", free: 15, locked: 0, usd_value: 57_000, ...syntheticFreshness(ts) },
    ];
  }

  getQuantLevels(): QuantLevelsContext {
    const ts = this.nowNs();
    const p = this.currentPrice;
    return {
      symbol: this.profile.symbol,
      levels: [
        { label: "R2", price: p * 1.02, kind: "resistance" },
        { label: "R1", price: p * 1.01, kind: "resistance" },
        { label: "Pivot", price: p, kind: "pivot" },
        { label: "S1", price: p * 0.99, kind: "support" },
        { label: "S2", price: p * 0.98, kind: "support" },
      ],
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getTickToTrade(): TickToTradeTrace {
    const ts = this.nowNs();
    const t2s = this.rng.range(50, 500);
    const s2g = this.rng.range(100, 800);
    const g2e = this.rng.range(200, 1500);
    return {
      trace_id: `trc_${this.tickCount}`,
      tick_receive_ts_ns: ts - (t2s + s2g + g2e) * 1000,
      signal_ts_ns: ts - (s2g + g2e) * 1000,
      gate_ts_ns: ts - g2e * 1000,
      execution_ts_ns: ts,
      tick_to_signal_us: t2s,
      signal_to_gate_us: s2g,
      gate_to_execution_us: g2e,
      total_tick_to_trade_us: t2s + s2g + g2e,
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }

  getRuntimeHealth(): RuntimeHealth {
    const ts = this.nowNs();
    const mkLane = (lane: string, healthy: boolean): LaneHealth => ({
      lane,
      status: healthy ? "healthy" : this.rng.pick(["stale", "degraded"]),
      last_heartbeat_ts_ns: healthy ? ts - this.rng.int(0, 2_000_000_000) : ts - this.rng.int(10_000_000_000, 30_000_000_000),
      age_ms: healthy ? this.rng.int(0, 2000) : this.rng.int(10_000, 30_000),
      stale: !healthy,
      missing: false,
      reason_code: healthy ? null : "HEARTBEAT_TIMEOUT",
    });
    return {
      run_main_strategy_signal: mkLane("run_main_strategy_signal", true),
      run_gate_engine: mkLane("run_gate_engine", true),
      run_execution_lane: mkLane("run_execution_lane", this.rng.bool(0.85)),
      ai_lane_advisory: mkLane("ai_lane_advisory", true),
      data_health: mkLane("data_health", true),
      ts_event_ns: ts,
      ...syntheticFreshness(ts),
    };
  }
}
