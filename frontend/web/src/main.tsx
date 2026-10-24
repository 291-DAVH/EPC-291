import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthGate, I18nProvider } from "@epc/ui";
import "@epc/ui/styles.css";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <I18nProvider>
      <AuthGate>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AuthGate>
    </I18nProvider>
  </React.StrictMode>,
);
