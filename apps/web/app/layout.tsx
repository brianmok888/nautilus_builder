import "antd/dist/reset.css";
import "./globals.css";
import { OperatorAppShell } from "../components/shell/OperatorAppShell";

export const metadata = {
  title: "Nautilus Builder",
  description:
    "Builder-side strategy authoring and observational workflow shell",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <OperatorAppShell>{children}</OperatorAppShell>
      </body>
    </html>
  );
}
