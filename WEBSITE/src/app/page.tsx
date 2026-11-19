"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  Cpu,
  ArrowRight,
  Camera,
  HardDrive,
  Wifi,
  Server,
  Lock,
  Sparkles,
  CheckCircle2,
  Building2,
  MessageCircle,
} from "lucide-react";
import { apiFetch, buildWhatsAppLink } from "@/lib/api";
import { Banner, Brand, Category, Product } from "@/types";
import ProductCard from "@/components/ProductCard";

interface HomePayload {
  business_name: string;
  whatsapp: string;
  applied_tier: string;
  banners: Banner[];
  categories: Category[];
  brands: Brand[];
  featured_products: Product[];
  bestsellers: Product[];
  new_arrivals: Product[];
  special_offers: Product[];
}

export default function HomePage() {
  const [data, setData] = useState<HomePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"featured" | "bestsellers" | "new" | "offers">("featured");

  useEffect(() => {
    apiFetch<HomePayload>("/catalog/home/")
      .then((res) => setData(res))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const displayedProducts = () => {
    if (!data) return [];
    if (activeTab === "bestsellers") return data.bestsellers;
    if (activeTab === "new") return data.new_arrivals;
    if (activeTab === "offers") return data.special_offers.length ? data.special_offers : data.featured_products;
    return data.featured_products;
  };

  return (
    <div className="space-y-20 pb-20">
      {/* 1. LUXURY CINEMATIC HERO SECTION */}
      <section className="relative overflow-hidden border-b border-slate-800/80 bg-gradient-to-b from-[#0A101F] via-[#07090E] to-[#07090E] pt-12 pb-20">
        <div className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-blue-600/15 blur-[130px]" />

        <div className="mx-auto max-w-7xl px-4">
          <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="lg:col-span-7 space-y-6"
            >
              <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3.5 py-1.5 text-xs font-semibold text-blue-400">
                <Sparkles className="h-3.5 w-3.5" />
                <span>ÉCOSYSTÈME DE SÉCURITÉ PROFESSIONNEL • STOCK TEMPS RÉEL</span>
              </div>

              <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl leading-[1.1]">
                La Haute Technologie en{" "}
                <span className="bg-gradient-to-r from-blue-400 via-sky-400 to-blue-600 bg-clip-text text-transparent">
                  Vidéosurveillance & CCTV
                </span>
              </h1>

              <p className="max-w-2xl text-base text-slate-300 sm:text-lg leading-relaxed">
                Caméras IP & HDCVI, enregistreurs intelligents XVR/NVR, disques durs WD Purple 24/7 et accessoires certifiés. Connecté directement à notre stock physique pour une disponibilité garantie.
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-2">
                <Link
                  href="/catalog"
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3.5 text-sm font-bold text-white shadow-xl shadow-blue-600/25 hover:bg-blue-500 transition-all"
                >
                  <span>Explorer le Catalogue</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>

                <Link
                  href="/kit-builder"
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-[#0F1420] px-6 py-3.5 text-sm font-bold text-sky-400 hover:border-sky-500/50 hover:bg-slate-900 transition-all"
                >
                  <Cpu className="h-4 w-4" />
                  <span>Créer mon Kit sur mesure</span>
                </Link>
              </div>

              <div className="grid grid-cols-3 gap-4 pt-6 border-t border-slate-800/80 text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Tarifs Public, Installateur & Gros</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Garantie Officielle Constructeur</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Retrait Magasin ou Livraison</span>
                </div>
              </div>
            </motion.div>

            {/* Right Architectural Visual */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6 }}
              className="lg:col-span-5"
            >
              <div className="relative overflow-hidden rounded-3xl border border-slate-800 bg-[#0F1420] p-6 shadow-2xl">
                <img
                  src="https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=1000&q=85"
                  alt="Système CCTV Professionnel"
                  className="h-72 w-full rounded-2xl object-cover"
                />
                <div className="mt-5 grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-slate-800 bg-[#07090E] p-3.5">
                    <span className="text-[11px] font-semibold uppercase text-blue-400">Accès Installateurs</span>
                    <p className="mt-1 text-xs text-slate-300">Remises professionnelles automatiques après validation.</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-[#07090E] p-3.5">
                    <span className="text-[11px] font-semibold uppercase text-emerald-400">Accès Revendeurs</span>
                    <p className="mt-1 text-xs text-slate-300">Grille tarifaire Gros synchronisée avec notre comptoir.</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* 2. PRODUCT CATEGORIES GRID */}
      <section className="mx-auto max-w-7xl px-4">
        <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-blue-400">
              Rayons Spécialisés
            </span>
            <h2 className="mt-1 text-2xl font-extrabold text-white sm:text-3xl">
              Catégories de Vidéosurveillance
            </h2>
          </div>
          <Link href="/catalog" className="text-sm font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1">
            Voir toutes les catégories <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {(data?.categories || []).slice(0, 12).map((cat) => (
            <Link
              key={cat.id}
              href={`/catalog?category=${cat.slug}`}
              className="group flex flex-col justify-between rounded-2xl border border-slate-800/90 bg-[#0F1420] p-4 transition-all hover:-translate-y-1 hover:border-blue-500/50 hover:bg-[#131B2E]"
            >
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600/15 text-blue-400 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                <Camera className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white group-hover:text-blue-400">
                  {cat.name}
                </h3>
                <p className="mt-1 text-[11px] text-slate-400">
                  {cat.product_count} référence{cat.product_count > 1 ? "s" : ""}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* 3. FEATURED / BESTSELLERS / NEW ARRIVALS / SPECIAL OFFERS TABS */}
      <section className="mx-auto max-w-7xl px-4">
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-blue-400">
              Sélection Officielle
            </span>
            <h2 className="mt-1 text-2xl font-extrabold text-white sm:text-3xl">
              Équipements CCTV & Stock Disponible
            </h2>
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { id: "featured", label: "Produits Vedettes" },
              { id: "bestsellers", label: "Meilleures Ventes" },
              { id: "new", label: "Nouveautés" },
              { id: "offers", label: "Offres Spéciales" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                  activeTab === t.id
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-600/25"
                    : "border border-slate-800 bg-[#0F1420] text-slate-300 hover:border-slate-700"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="h-80 animate-pulse rounded-2xl border border-slate-800 bg-[#0F1420]" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {displayedProducts().map((prod) => (
              <ProductCard key={prod.id} product={prod} />
            ))}
          </div>
        )}
      </section>

      {/* 4. CCTV SOLUTIONS & KIT BUILDER BANNER */}
      <section className="mx-auto max-w-7xl px-4">
        <div className="overflow-hidden rounded-3xl border border-blue-500/30 bg-gradient-to-r from-[#0D1527] via-[#0F1B33] to-[#0A101D] p-8 sm:p-12">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 items-center">
            <div className="lg:col-span-8 space-y-4">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-500/20 px-3 py-1 text-xs font-bold text-sky-300">
                <Cpu className="h-3.5 w-3.5" /> OUTIL EXCLUSIF D&apos;INGÉNIERIE CCTV
              </span>
              <h2 className="text-2xl font-extrabold text-white sm:text-4xl">
                Composez votre Kit de Surveillance Complet en 6 Étapes
              </h2>
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Sélectionnez vos caméras, votre enregistreur DVR/XVR ou NVR, le disque dur WD Purple, l&apos;alimentation 12V et la connectique BNC. Notre moteur vérifie automatiquement la compatibilité technique et calcule votre tarif immédiat.
              </p>
              <div className="pt-2">
                <Link
                  href="/kit-builder"
                  className="inline-flex items-center gap-2 rounded-xl bg-sky-500 px-6 py-3.5 text-sm font-extrabold text-slate-950 hover:bg-sky-400 transition-colors"
                >
                  <span>Lancer le Configurateur de Kit</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>

            <div className="lg:col-span-4 grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-2xl border border-slate-800 bg-[#07090E]/80 p-4">
                <Server className="h-6 w-6 text-blue-400 mb-2" />
                <div className="font-bold text-white">Vérification Canaux</div>
                <p className="mt-1 text-slate-400">Contrôle auto 4 / 8 / 16 / 32 canaux XVR & NVR.</p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-[#07090E]/80 p-4">
                <HardDrive className="h-6 w-6 text-sky-400 mb-2" />
                <div className="font-bold text-white">Calcul Stockage</div>
                <p className="mt-1 text-slate-400">Recommandation capacité WD Purple 24/7.</p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-[#07090E]/80 p-4">
                <Lock className="h-6 w-6 text-emerald-400 mb-2" />
                <div className="font-bold text-white">Tarif Dynamique</div>
                <p className="mt-1 text-slate-400">Applique votre remise Installateur ou Revendeur.</p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-[#07090E]/80 p-4">
                <ShieldCheck className="h-6 w-6 text-amber-400 mb-2" />
                <div className="font-bold text-white">Prêt à Poser</div>
                <p className="mt-1 text-slate-400">Ajout en 1 clic au panier avec tous les accessoires.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. ARCHITECTURAL CCTV SOLUTIONS BY SECTOR */}
      <section className="mx-auto max-w-7xl px-4">
        <div className="mb-8">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-400">
            Applications Terrain
          </span>
          <h2 className="mt-1 text-2xl font-extrabold text-white sm:text-3xl">
            Solutions de Sécurité par Secteur
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {[
            {
              title: "Résidentiel & Villas",
              desc: "Protection périmétrique ColorVu / Full-Color nocturne, caméras Wi-Fi motorisées et visualisation mobile DMSS / Hik-Connect.",
              icon: Wifi,
            },
            {
              title: "Commerces, Supérettes & Bureaux",
              desc: "Systèmes 4 à 16 caméras haute définition avec enregistrement continu sur disque WD Purple et déport HDMI KVM.",
              icon: Building2,
            },
            {
              title: "Usines, Dépôts & Chantiers",
              desc: "Architectures IP NVR PoE longue portée, dômes PTZ motorisés x25 et détection intelligente Humain/Véhicule.",
              icon: ShieldCheck,
            },
          ].map((sol, i) => {
            const Icon = sol.icon;
            return (
              <div
                key={i}
                className="rounded-2xl border border-slate-800 bg-[#0F1420] p-6 space-y-3 hover:border-blue-500/40 transition-colors"
              >
                <div className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600/15 text-blue-400">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-white">{sol.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{sol.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* 6. BRANDS & WHATSAPP CTA */}
      <section className="mx-auto max-w-7xl px-4">
        <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
            <div>
              <h3 className="text-lg font-bold text-white">Marques Partenaires Distribuées</h3>
              <p className="text-xs text-slate-400">Matériel original avec numéros de série traçables</p>
            </div>
            <div className="flex flex-wrap gap-3">
              {(data?.brands || []).map((b) => (
                <Link
                  key={b.id}
                  href={`/catalog?brand=${b.slug}`}
                  className="rounded-xl border border-slate-800 bg-[#0F1420] px-4 py-2 text-xs font-bold text-slate-200 hover:border-blue-500/50 hover:text-blue-400"
                >
                  {b.name}
                </Link>
              ))}
            </div>
          </div>

          <div className="mt-6 flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="text-sm text-slate-300">
              Besoin d&apos;une cotation rapide pour un cahier des charges ou une commande en gros ?
            </div>
            <a
              href={buildWhatsAppLink(
                data?.whatsapp || "+213550000000",
                "Bonjour LOGISZ, je souhaite un devis professionnel pour du matériel CCTV."
              )}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-emerald-500"
            >
              <MessageCircle className="h-4 w-4" />
              Contacter le Service Pro sur WhatsApp
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

