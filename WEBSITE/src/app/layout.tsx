import type { Metadata } from "next";
import "./globals.css";
import { StoreProvider } from "@/context/StoreContext";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "LOGISZ SECURITY | Systèmes de Vidéosurveillance & CCTV Professionnels",
  description:
    "Catalogue officiel de caméras de surveillance IP & HDCVI, enregistreurs XVR/NVR, disques durs WD Purple et accessoires CCTV. Tarifs dédiés Installateurs & Revendeurs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="dark">
      <body className="min-h-screen flex flex-col bg-[#07090E] text-slate-100 antialiased">
        <StoreProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </StoreProvider>
      </body>
    </html>
  );
}

