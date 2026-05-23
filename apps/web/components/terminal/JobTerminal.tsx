import { parseTerminalCommand } from "./commands";

export const JobTerminal = () => {
  const command = parseTerminalCommand("status");
  return `JobTerminal: observational only, not a shell (${command.reason})`;
};
