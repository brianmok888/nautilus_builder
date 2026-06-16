"use client";

import { ModelConfigTabs } from "../../../components/config/ModelConfigTabs";
import { PageHeader } from "../../../components/ui/PageHeader";
import { SettingOutlined } from "@ant-design/icons";

export default function ConfigPage() {
  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Model configuration and adapter settings. Browser credential entry is disabled."
        icon={<SettingOutlined />}
      />
      <ModelConfigTabs />
    </div>
  );
}
