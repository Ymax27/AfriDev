import { Suspense, useEffect } from "react";
import { RouterProvider } from "react-router-dom";

import { AppProviders } from "@/app/providers";
import { router } from "@/app/router";
import { Spinner } from "@/components/ui";
import { useUiStore } from "@/stores/ui-store";

function useLowBandwidthMode() {
  const { lightweightMode, setLightweightMode } = useUiStore();

  useEffect(() => {
    // Respect the browser's data-saver signal on first visit.
    const connection = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
    if (connection?.saveData && !lightweightMode) {
      setLightweightMode(true);
      return;
    }
    document.documentElement.dataset.lightweight = lightweightMode ? "true" : "false";
  }, [lightweightMode, setLightweightMode]);
}

export default function App() {
  useLowBandwidthMode();

  return (
    <AppProviders>
      <Suspense fallback={<Spinner label="…" />}>
        <RouterProvider router={router} />
      </Suspense>
    </AppProviders>
  );
}
