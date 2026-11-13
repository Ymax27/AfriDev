import { Suspense } from "react";
import { RouterProvider } from "react-router-dom";

import { AppProviders } from "@/app/providers";
import { router } from "@/app/router";
import { Spinner } from "@/components/ui";

export default function App() {
  return (
    <AppProviders>
      <Suspense fallback={<Spinner label="…" />}>
        <RouterProvider router={router} />
      </Suspense>
    </AppProviders>
  );
}
