"use client";

import React from "react";
import type { AccountSnapshot } from "../../lib/tradehud/types";
import { fmtNotional, fmtSigned } from "../../lib/tradehud/number-format";

interface AccountSummaryPanelProps {
  account: AccountSnapshot | null;
}

function Row({
  label,
  value,
  signed = false,
  currency,
}: {
  label: string;
  value: number;
  signed?: boolean;
  currency?: string;
}) {
  const positive = value >= 0;
  const cls = signed ? (positive ? "tradehud-pos" : "tradehud-neg") : undefined;
  return (
    <div className="tradehud-kv">
      <span className="tradehud-muted">{label}</span>
      <span className={cls}>
        {signed ? fmtSigned(value) : fmtNotional(value)}
        {currency ? <span className="tradehud-muted"> {currency}</span> : null}
      </span>
    </div>
  );
}

export const AccountSummaryPanel: React.FC<AccountSummaryPanelProps> = ({ account }) => {
  const missing =
    !account || (account as any).missing === true || (account as any).source_available === false;

  if (missing || !account) {
    return (
      <section className="tradehud-panel">
        <header className="tradehud-panel-header">
          <span className="tradehud-panel-title">Account</span>
        </header>
        <div className="tradehud-panel-body">
          <div className="tradehud-missing-text">Account data unavailable</div>
        </div>
      </section>
    );
  }

  const ccy = account.currency;

  return (
    <section className="tradehud-panel">
      <header className="tradehud-panel-header">
        <span className="tradehud-panel-title">Account</span>
        <span className="tradehud-panel-badge tradehud-panel-badge-info">
          {account.account_id}
        </span>
      </header>
      <div className="tradehud-panel-body">
        <Row label="Balance" value={account.balance} currency={ccy} />
        <Row label="Equity" value={account.equity} currency={ccy} />
        <Row label="Avail Margin" value={account.available_margin} currency={ccy} />
        <Row label="Margin Used" value={account.margin_used} currency={ccy} />
        <Row label="uPNL" value={account.unrealized_pnl} signed currency={ccy} />
        <Row label="rPNL" value={account.realized_pnl} signed currency={ccy} />
      </div>
    </section>
  );
};

export default AccountSummaryPanel;
