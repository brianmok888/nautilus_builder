import { describe, expect, it } from "vitest";

import { JobTerminal } from "./JobTerminal";
import { parseTerminalCommand } from "./commands";

describe("JobTerminal", () => {
  it("renders real job/event/cancel contract names without becoming a shell", () => {
    const rendered = JobTerminal({ jobId: "bt_123", status: "queued", eventCount: 2 });

    expect(rendered).toContain("bt_123");
    expect(rendered).toContain("queued");
    expect(rendered).toContain("2 runtime events");
    expect(rendered).toContain("fetchBacktestJob");
    expect(rendered).toContain("fetchBacktestJobEvents");
    expect(rendered).toContain("cancelBacktestJob");
    expect(rendered).toContain("observational only");
    expect(rendered).not.toContain("bash");
    expect(rendered).not.toContain("docker");
  });

  it("allows only bounded observational commands", () => {
    expect(parseTerminalCommand("request cancel")).toEqual({ allowed: true, reason: "observational command" });
    expect(parseTerminalCommand("tail logs")).toEqual({ allowed: true, reason: "observational command" });
    expect(parseTerminalCommand("bash -lc env").allowed).toBe(false);
    expect(parseTerminalCommand("python run.py").allowed).toBe(false);
  });
});
