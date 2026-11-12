import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { SkeletonCheckPage } from "./features/survey/pages/SkeletonCheckPage";

const root = document.getElementById("root");
if (root === null) {
  throw new Error("No se encontró el elemento #root.");
}

createRoot(root).render(
  <StrictMode>
    <SkeletonCheckPage />
  </StrictMode>,
);
