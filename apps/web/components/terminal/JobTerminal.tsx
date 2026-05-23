import { parseTerminalCommand } from "./commands";
import { cancelBacktestJob, fetchBacktestJob, fetchBacktestJobEvents } from "../../lib/api";

type JobTerminalProps = {
  jobId?: string;
  status?: string;
  eventCount?: number;
};

export const JobTerminal = ({ jobId = "pending", status = "unknown", eventCount = 0 }: JobTerminalProps = {}) => {
  const command = parseTerminalCommand("status");
  const contracts = [fetchBacktestJob.name, fetchBacktestJobEvents.name, cancelBacktestJob.name];
  return `JobTerminal ${jobId}: ${status}; ${eventCount} runtime events; contracts ${contracts.join(", ")}; observational only, not a shell (${command.reason})`;
};
