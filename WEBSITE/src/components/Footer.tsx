"use client";

import React from "react";
import Link from "next/link";
import { Shield, PhoneCall, MapPin, MessageCircle, CheckCircle } from "lucide-react";
import { buildWhatsAppLink } from "@/lib/api";

export default function Footer() {
  const whatsapp = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "+213550000000";
  const waUrl = buildWhatsAppLink(
    whatsapp,
    "Bonjour LOGISZ CCTV, je souhaite obtenir un conseil ou un devis pour du matériel de vidéosurveillance."
  );

  return (
    <footer className="border-t border-slate-800/80 bg-[#05070B] text-slate-400">
      <div className="mx-auto max-w-7xl px-4 py-14">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-4">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-extrabold text-white">
                LOGI<span className="text-blue-500">SZ</span> SECURITY
              </span>
            </div>
            <p className="text-sm leading-relaxed text-slate-400">
              Distributeur officiel de systèmes de vidéosurveillance, caméras IP & HDCVI, enregistreurs XVR/NVR, disques WD Purple et accessoires professionnels.
            </p>
            <div className="flex items-center gap-2 text-xs text-emerald-400">
              <CheckCircle className="h-4 w-4" />
              <span>Synchronisé avec le stock physique LOGISZ POS</span>
            </div>
          </div>

          <div>
            <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-white">
              Catégories CCTV
            </h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link href="/catalog?category=ip-cameras" className="hover:text-blue-400">Caméras IP PoE</Link></li>
              <li><Link href="/catalog?category=analog-cameras" className="hover:text-blue-400">Caméras Analogiques HD</Link></li>
              <li><Link href="/catalog?category=wi-fi-cameras" className="hover:text-blue-400">Caméras Wi-Fi 360°</Link></li>
              <li><Link href="/catalog?category=dvr" className="hover:text-blue-400">Enregistreurs DVR / XVR</Link></li>
              <li><Link href="/catalog?category=surveillance-hard-drives" className="hover:text-blue-400">Disques Durs WD Purple</Link></li>
              <li><Link href="/catalog?category=power-supplies" className="hover:text-blue-400">Alimentations & Connectique</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-white">
              Espace Professionnel
            </h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link href="/account" className="hover:text-blue-400">Compte Installateur Agréé</Link></li>
              <li><Link href="/account" className="hover:text-blue-400">Compte Revendeur / Grossiste</Link></li>
              <li><Link href="/kit-builder" className="hover:text-blue-400">Configurateur de Kit sur mesure</Link></li>
              <li><Link href="/cart" className="hover:text-blue-400">Suivi de Commande en ligne</Link></li>
              <li><Link href="/admin" className="hover:text-blue-400">Portail Administration</Link></li>
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-white">
              Assistance & Devis Direct
            </h4>
            <p className="flex items-center gap-2 text-sm">
              <PhoneCall className="h-4 w-4 text-blue-400" />
              <span>Service Commercial : {whatsapp}</span>
            </p>
            <p className="flex items-center gap-2 text-sm">
              <MapPin className="h-4 w-4 text-blue-400" />
              <span>Retrait en magasin & Livraison 58 Wilayas</span>
            </p>
            <a
              href={waUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-emerald-500 transition-colors"
            >
              <MessageCircle className="h-4 w-4" />
              Discuter sur WhatsApp
            </a>
          </div>
        </div>

        <div className="mt-10 border-t border-slate-900 pt-6 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} LOGISZ CCTV & Security Ecosystem. Tous droits réservés.
        </div>
      </div>

      {/* Floating WhatsApp CTA */}
      <a
        href={waUrl}
        target="_blank"
        rel="noreferrer"
        title="Contactez-nous sur WhatsApp"
        className="fixed bottom-6 right-6 z-40 flex h-13 w-13 items-center justify-center rounded-full bg-emerald-500 p-3.5 text-white shadow-2xl shadow-emerald-600/40 hover:scale-110 transition-transform"
      >
        <MessageCircle className="h-6 w-6" />
      </a>
    </footer>
  );
}

