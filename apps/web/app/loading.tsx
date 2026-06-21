import { Card, Skeleton, Space, Spin } from "antd";

export default function Loading() {
  return (
    <Space orientation="vertical" size="middle" style={{ width: "100%", padding: 16 }}>
      <Card size="small">
        <Skeleton active paragraph={{ rows: 3 }} />
      </Card>
      <Card size="small">
        <Skeleton active paragraph={{ rows: 2 }} />
      </Card>
      <div style={{ textAlign: "center", padding: 24 }}>
        <Spin size="large" />
      </div>
    </Space>
  );
}
