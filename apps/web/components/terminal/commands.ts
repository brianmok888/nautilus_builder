export const ALLOWED_TERMINAL_COMMANDS = ["help", "status", "show config", "show validation", "show metrics", "tail logs", "request cancel"] as const;

const FORBIDDEN_TERMINAL_COMMANDS = ["bash", "zsh", "python", "curl", "wget", "docker", "kubectl", "env", "ssh"];

export function parseTerminalCommand(command: string): { allowed: boolean; reason: string } {
  const normalized = command.trim().toLowerCase();
  if (FORBIDDEN_TERMINAL_COMMANDS.some((forbidden) => normalized.includes(forbidden))) {
    return { allowed: false, reason: "forbidden shell/runtime command" };
  }
  return { allowed: ALLOWED_TERMINAL_COMMANDS.includes(normalized as (typeof ALLOWED_TERMINAL_COMMANDS)[number]), reason: "observational command" };
}
