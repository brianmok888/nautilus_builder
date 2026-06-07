import { Alert } from "antd";

export function BuilderSafetyBanner() {
  return (
    <Alert
      className="nb-safety-banner"
      type="info"
      showIcon
      message="Builder-only mode"
      description="This UI creates and reviews strategy drafts, validation results, compiler artifacts, replay evidence, and promotion requests. It does not submit live orders."
    />
  );
}
