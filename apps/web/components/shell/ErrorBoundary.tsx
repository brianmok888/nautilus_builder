"use client";

import { Component, type ReactNode } from "react";
import { Alert, Button, Card, Space, Typography } from "antd";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card size="small" style={{ margin: 16 }}>
          <Space orientation="vertical" style={{ width: "100%" }}>
            <Typography.Title level={4}>
              {this.props.fallbackTitle ?? "Something went wrong"}
            </Typography.Title>
            <Alert
              type="error"
              showIcon
              message={this.state.error?.message ?? "An unexpected error occurred"}
              description="This section encountered an error. Try refreshing the page."
            />
            <Button
              type="primary"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Retry
            </Button>
          </Space>
        </Card>
      );
    }
    return this.props.children;
  }
}
