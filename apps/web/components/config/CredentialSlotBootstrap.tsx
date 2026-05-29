"use client";

import { useState } from "react";
import { Alert, Button, Card, Form, Input, Space, Tag, Typography } from "antd";
import { saveExecutionLaneCredentialSlot } from "../../lib/api";
import type { ExecutionCredentialSlot } from "../../lib/types";

export const CredentialSlotBootstrap = () => {
  const [venue, setVenue] = useState("");
  const [requestedBy, setRequestedBy] = useState("");
  const [variable1, setVariable1] = useState("");
  const [value1, setValue1] = useState("");
  const [variable2, setVariable2] = useState("");
  const [value2, setValue2] = useState("");
  const [credentialSlot, setCredentialSlot] = useState<ExecutionCredentialSlot | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSave = Boolean(venue && variable1 && value1);

  async function onSave() {
    setError(null);
    setSaving(true);
    try {
      const credentialValues: Record<string, string> = { [variable1]: value1 };
      if (variable2 && value2) credentialValues[variable2] = value2;
      const slot = await saveExecutionLaneCredentialSlot({
        tenant_id: "tenant_001",
        project_id: "project_001",
        runtime_profile_id: "rp_paper_001",
        adapter_id: venue.toUpperCase(),
        venue,
        lane_mode: "paper",
        requested_by: requestedBy,
        credential_values: credentialValues,
      });
      setCredentialSlot(slot);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card title="Credential Slot Bootstrap" size="small">
      <Typography.Paragraph type="secondary">
        Local/dev bootstrap only: the browser sends venue-scoped credential variables once,
        the backend writes them to a gitignored local env file, and the UI keeps only a credential_slot_ref.
        Secrets are cleared after save and never echoed in reports.
      </Typography.Paragraph>
      <Form layout="vertical" className="form-grid">
        <Form.Item label="Venue">
          <Input placeholder="BINANCE" value={venue} onChange={(e) => setVenue(e.target.value)} />
        </Form.Item>
        <Form.Item label="Requested by">
          <Input value={requestedBy} onChange={(e) => setRequestedBy(e.target.value)} />
        </Form.Item>
        <Form.Item label="Credential variable 1">
          <Input placeholder="BINANCE_API_KEY" value={variable1} onChange={(e) => setVariable1(e.target.value)} />
        </Form.Item>
        <Form.Item label="Credential value 1">
          <Input.Password value={value1} onChange={(e) => setValue1(e.target.value)} />
        </Form.Item>
        <Form.Item label="Credential variable 2">
          <Input placeholder="BINANCE_API_SECRET" value={variable2} onChange={(e) => setVariable2(e.target.value)} />
        </Form.Item>
        <Form.Item label="Credential value 2">
          <Input.Password value={value2} onChange={(e) => setValue2(e.target.value)} />
        </Form.Item>
      </Form>
      <Space wrap>
        <Button disabled={!canSave} loading={saving} onClick={onSave}>
          Save credential slot
        </Button>
        <Tag color="blue">writes .env.execution.local</Tag>
        <Tag color="green">browser secret echo: false</Tag>
      </Space>
      {credentialSlot ? (
        <Alert
          showIcon
          type="success"
          title="Credential slot ready"
          style={{ marginTop: 12 }}
          description={
            <Space orientation="vertical" size={2}>
              <Typography.Text>{credentialSlot.credential_slot_ref}</Typography.Text>
              <Typography.Text>redacted keys: {credentialSlot.redacted_keys.join(", ")}</Typography.Text>
              <Typography.Text>env file: {credentialSlot.env_file_path}</Typography.Text>
            </Space>
          }
        />
      ) : null}
      {error ? <Alert type="error" showIcon title="Save failed" description={error} style={{ marginTop: 12 }} /> : null}
    </Card>
  );
};
