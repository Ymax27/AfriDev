import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "@/app/App";
import "@/i18n";
import "@/styles/index.css";
import { useAuthStore } from "@/stores/auth-store";

const container = document.getElementById("root");
if (!container) throw new Error("Root container missing");

void useAuthStore.getState().hydrate();

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
