/**
 * Heatmap buffer for Bookmap-style canvas rendering.
 * Uses a 2D Float32Array grid indexed by [price_row][time_col].
 * Ring-shifts time columns to avoid reallocation.
 */
import { HEATMAP_TIME_COLS, HEATMAP_PRICE_ROWS } from "./types";

export interface HeatmapConfig {
  priceRows: number;
  timeCols: number;
  priceMin: number;
  priceMax: number;
}

export class HeatmapBuffer {
  readonly cfg: HeatmapConfig;
  private bidGrid: Float32Array;
  private askGrid: Float32Array;
  private timeHead = 0;
  private filledCols = 0;
  private colTimestamps: Float64Array;

  constructor(cfg?: Partial<HeatmapConfig>) {
    this.cfg = {
      priceRows: cfg?.priceRows ?? HEATMAP_PRICE_ROWS,
      timeCols: cfg?.timeCols ?? HEATMAP_TIME_COLS,
      priceMin: cfg?.priceMin ?? 0,
      priceMax: cfg?.priceMax ?? 1,
    };
    const total = this.cfg.priceRows * this.cfg.timeCols;
    this.bidGrid = new Float32Array(total);
    this.askGrid = new Float32Array(total);
    this.colTimestamps = new Float64Array(this.cfg.timeCols);
  }

  private priceToRow(price: number): number {
    const range = this.cfg.priceMax - this.cfg.priceMin;
    if (range <= 0) return 0;
    const row = Math.floor(((price - this.cfg.priceMin) / range) * this.cfg.priceRows);
    return Math.max(0, Math.min(this.cfg.priceRows - 1, row));
  }

  advanceTime(ts: number): void {
    this.timeHead = (this.timeHead + 1) % this.cfg.timeCols;
    const colBase = this.timeHead * this.cfg.priceRows;
    // Clear the new column
    this.bidGrid.fill(0, colBase, colBase + this.cfg.priceRows);
    this.askGrid.fill(0, colBase, colBase + this.cfg.priceRows);
    this.colTimestamps[this.timeHead] = ts;
    if (this.filledCols < this.cfg.timeCols) this.filledCols++;
  }

  addBidLevel(price: number, intensity: number): void {
    const row = this.priceToRow(price);
    const idx = this.timeHead * this.cfg.priceRows + row;
    this.bidGrid[idx] += intensity;
  }

  addAskLevel(price: number, intensity: number): void {
    const row = this.priceToRow(price);
    const idx = this.timeHead * this.cfg.priceRows + row;
    this.askGrid[idx] += intensity;
  }

  getCell(row: number, col: number): { bid: number; ask: number } {
    const actualCol = (this.timeHead + 1 + col) % this.cfg.timeCols;
    const idx = actualCol * this.cfg.priceRows + row;
    return { bid: this.bidGrid[idx], ask: this.askGrid[idx] };
  }

  /**
   * Iterate columns from oldest to newest for rendering.
   * Returns a typed accessor for efficient canvas painting.
   */
  getRenderData(): {
    priceRows: number;
    timeCols: number;
    filledCols: number;
    getIntensity: (row: number, col: number) => { bid: number; ask: number };
  } {
    const head = this.timeHead;
    const filled = this.filledCols;
    const bid = this.bidGrid;
    const ask = this.askGrid;
    const rows = this.cfg.priceRows;
    const cols = this.cfg.timeCols;

    return {
      priceRows: rows,
      timeCols: cols,
      filledCols: filled,
      getIntensity(row: number, col: number) {
        // col 0 = oldest, col filledCols-1 = newest
        const actualCol = (head + 1 + col) % cols;
        const idx = actualCol * rows + row;
        return { bid: bid[idx], ask: ask[idx] };
      },
    };
  }

  setPriceRange(min: number, max: number): void {
    if (min >= max) return;
    this.cfg.priceMin = min;
    this.cfg.priceMax = max;
  }

  get currentPriceRange(): { min: number; max: number } {
    return { min: this.cfg.priceMin, max: this.cfg.priceMax };
  }
}
