import { CredentialSlotBootstrap } from "../../components/config/CredentialSlotBootstrap";
import { ModelConfigTabs } from "../../components/config/ModelConfigTabs";

export default function ConfigPage() {
  return (
    <main className="app-shell">
      <ModelConfigTabs />
      <CredentialSlotBootstrap />
    </main>
  );
}
