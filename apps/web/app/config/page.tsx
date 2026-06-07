"use client";

import { CredentialSlotBootstrap } from "../../components/config/CredentialSlotBootstrap";
import { ModelConfigTabs } from "../../components/config/ModelConfigTabs";
import { PageHeader } from "../../components/ui/PageHeader";
import { SettingOutlined } from "@ant-design/icons";

export default function ConfigPage() {
  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Model configuration, credential slots, and adapter settings."
        icon={<SettingOutlined />}
      />
      <ModelConfigTabs />
      <CredentialSlotBootstrap />
    </div>
  );
}
