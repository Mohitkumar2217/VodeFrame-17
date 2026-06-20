import type { Metadata } from "next";
import { PortalDashboard } from "../../components/PortalDashboard";
import { DocumentProvider } from "../../contexts/DocumentContext";

export const metadata: Metadata = {
  title: "Assessment Portal | MDoNER",
  description: "AI-powered DPR evaluation.",
};

export default function PortalPage() {
  return ( 
    <DocumentProvider>
      <PortalDashboard />
    </DocumentProvider> 
  );
}
