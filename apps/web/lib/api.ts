export async function fetchAdapters() {
  const response = await fetch("/api/adapters");
  return response.json();
}

export async function fetchStrategies() {
  const response = await fetch("/api/strategies");
  return response.json();
}

export async function validateBacktestProfile(profile: Record<string, string>) {
  const response = await fetch("/api/backtest-profiles/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  return response.json();
}
