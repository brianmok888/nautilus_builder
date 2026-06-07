import "antd/dist/reset.css";
import "./globals.css";
import { BuilderThemeProvider } from "../components/theme/BuilderThemeProvider";
import { BuilderShell } from "../components/shell/BuilderShell";

export const metadata = {
  title: "Nautilus Builder",
  description:
    "Builder-side strategy authoring and observational workflow shell",
};

const assetFailureReloadGuard = `
(function () {
  var retriedKey = "nautilus-builder-static-asset-retry";
  function isNextStaticAsset(target) {
    var url = target && (target.src || target.href);
    return typeof url === "string" && url.indexOf("/_next/static/") !== -1;
  }
  function retryWithCacheBust() {
    try {
      if (window.sessionStorage.getItem(retriedKey) === "1") return;
      window.sessionStorage.setItem(retriedKey, "1");
      var url = new URL(window.location.href);
      url.searchParams.set("nb_asset_retry", String(Date.now()));
      window.location.replace(url.toString());
    } catch (_error) {
      window.location.reload();
    }
  }
  window.addEventListener(
    "error",
    function (event) {
      if (isNextStaticAsset(event.target)) retryWithCacheBust();
    },
    true,
  );
  window.addEventListener("load", function () {
    try {
      window.sessionStorage.removeItem(retriedKey);
    } catch (_error) {
      // Ignore storage failures; successful load is already enough.
    }
  });
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <script dangerouslySetInnerHTML={{ __html: assetFailureReloadGuard }} />
        <BuilderThemeProvider>
          <BuilderShell>{children}</BuilderShell>
        </BuilderThemeProvider>
      </body>
    </html>
  );
}
