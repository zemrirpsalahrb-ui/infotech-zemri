"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  ShoppingCart,
  Plus,
  Minus,
  Sparkles,
} from "lucide-react";
import { apiFetch, formatMoney } from "@/lib/api";
import { Product } from "@/types";
import { useStore } from "@/context/StoreContext";

interface KitCatalog {
  applied_tier: string;
  cameras: Product[];
  recorders: Product[];
  hdds: Product[];
  psus: Product[];
  cables: Product[];
  connectors: Product[];
  accessories: Product[];
}

interface EvaluationResult {
  applied_tier: string;
  is_compatible: boolean;
  total_cameras: number;
  recorder_channels: number;
  package_total: number;
  warnings: string[];
  recommendations: string[];
}

export default function KitBuilderPage() {
  const { addToCart } = useStore();
  const router = useRouter();
  const [catalog, setCatalog] = useState<KitCatalog | null>(null);
  const [selected, setSelected] = useState<Record<number, number>>({});
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [activeStep, setActiveStep] = useState<
    "cameras" | "recorders" | "hdds" | "psus" | "cables" | "connectors" | "accessories"
  >("cameras");

  useEffect(() => {
    apiFetch<KitCatalog>("/kit-builder/")
      .then((res) => setCatalog(res))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const items = Object.entries(selected)
      .filter(([, q]) => q > 0)
      .map(([pid, quantity]) => ({ product_id: Number(pid), quantity }));

    if (items.length === 0) {
      setEvaluation(null);
      return;
    }

    apiFetch<EvaluationResult>("/kit-builder/", {
      method: "POST",
      body: JSON.stringify({ items }),
    })
      .then((res) => setEvaluation(res))
      .catch(() => {});
  }, [selected]);

  const setQty = (productId: number, qty: number) => {
    setSelected((prev) => {
      const next = { ...prev };
      if (qty <= 0) delete next[productId];
      else next[productId] = qty;
      return next;
    });
  };

  const allProductsMap = (): Map<number, Product> => {
    const map = new Map<number, Product>();
    if (!catalog) return map;
    [
      ...catalog.cameras,
      ...catalog.recorders,
      ...catalog.hdds,
      ...catalog.psus,
      ...catalog.cables,
      ...catalog.connectors,
      ...catalog.accessories,
    ].forEach((p) => map.set(p.id, p));
    return map;
  };

  const addKitToCart = () => {
    const map = allProductsMap();
    Object.entries(selected).forEach(([pid, q]) => {
      const prod = map.get(Number(pid));
      if (prod && q > 0) {
        addToCart(prod, q);
      }
    });
    router.push("/cart");
  };

  const steps = [
    { key: "cameras", label: "1. Caméras" },
    { key: "recorders", label: "2. DVR / XVR / NVR" },
    { key: "hdds", label: "3. Disque Dur 24/7" },
    { key: "psus", label: "4. Alimentation" },
    { key: "cables", label: "5. Câbles" },
    { key: "connectors", label: "6. Connecteurs BNC" },
    { key: "accessories", label: "7. Accessoires" },
  ] as const;

  const currentList: Product[] = catalog ? (catalog[activeStep] || []) : [];
  const pMap = allProductsMap();

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 space-y-8">
      {/* Header */}
      <div className="rounded-3xl border border-blue-500/30 bg-gradient-to-r from-[#0C1426] to-[#080C16] p-6 sm:p-8">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-sky-400">
          <Cpu className="h-4 w-4" />
          <span>Configurateur Intelligent de Kit Vidéosurveillance</span>
        </div>
        <h1 className="mt-2 text-2xl font-extrabold text-white sm:text-3xl">
          Composez votre Pack CCTV Complet sur Mesure
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-slate-300">
          Sélectionnez vos composants étape par étape. Le système vérifie la compatibilité (nombre de canaux, technologie IP/HDCVI, stockage et alimentation) et applique votre tarif {catalog?.applied_tier || "PUBLIC"}.
        </p>

        {/* Stepper */}
        <div className="mt-6 flex flex-wrap gap-2">
          {steps.map((s) => (
            <button
              key={s.key}
              onClick={() => setActiveStep(s.key)}
              className={`rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeStep === s.key
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
                  : "border border-slate-800 bg-[#0F1420] text-slate-300 hover:border-slate-700"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left: Component Selection */}
        <div className="lg:col-span-8 space-y-4">
          {currentList.length === 0 ? (
            <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-10 text-center text-xs text-slate-400">
              Aucun équipement trouvé dans cette catégorie.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {currentList.map((prod) => {
                const count = selected[prod.id] || 0;
                return (
                  <div
                    key={prod.id}
                    className={`flex flex-col justify-between rounded-2xl border p-4 transition-all ${
                      count > 0
                        ? "border-blue-500 bg-blue-950/20"
                        : "border-slate-800 bg-[#0F1420]"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span className="font-mono text-blue-400">Réf: {prod.reference}</span>
                        <span>{prod.kit_technology}</span>
                      </div>
                      <h3 className="mt-1 text-sm font-bold text-white">{prod.name}</h3>
                      <p className="mt-1 text-xs text-slate-400 line-clamp-2">
                        {prod.short_description}
                      </p>
                    </div>

                    <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-800/80">
                      <span className="text-base font-extrabold text-white">
                        {formatMoney(prod.effective_price)}
                      </span>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setQty(prod.id, count - 1)}
                          className="rounded-lg border border-slate-700 bg-[#07090E] p-1.5 text-slate-300 hover:text-white"
                        >
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                        <span className="w-6 text-center text-xs font-extrabold text-white">
                          {count}
                        </span>
                        <button
                          onClick={() => setQty(prod.id, count + 1)}
                          className="rounded-lg bg-blue-600 p-1.5 text-white hover:bg-blue-500"
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Live Compatibility & Package Summary */}
        <div className="lg:col-span-4">
          <div className="sticky top-24 rounded-3xl border border-slate-800 bg-[#0F1420] p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-extrabold text-white">Résumé de votre Kit CCTV</h2>
              <span className="rounded-md bg-blue-600/20 px-2 py-0.5 text-[10px] font-bold text-blue-400">
                {catalog?.applied_tier || "PUBLIC"}
              </span>
            </div>

            {Object.keys(selected).length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">
                Sélectionnez vos caméras et votre enregistreur à gauche pour démarrer la vérification de compatibilité.
              </p>
            ) : (
              <>
                <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                  {Object.entries(selected).map(([pid, q]) => {
                    const p = pMap.get(Number(pid));
                    if (!p) return null;
                    return (
                      <div key={pid} className="flex items-center justify-between text-xs border-b border-slate-800/60 pb-2">
                        <div>
                          <div className="font-semibold text-white">{p.name}</div>
                          <div className="text-slate-400">
                            {q} × {formatMoney(p.effective_price)}
                          </div>
                        </div>
                        <span className="font-bold text-slate-200">
                          {formatMoney(p.effective_price * q)}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Compatibility Status */}
                {evaluation && (
                  <div className="space-y-3">
                    {evaluation.is_compatible ? (
                      <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs font-semibold text-emerald-300">
                        <CheckCircle2 className="h-4 w-4 shrink-0" />
                        <span>Configuration compatible ({evaluation.total_cameras} caméras / {evaluation.recorder_channels || "—"} canaux)</span>
                      </div>
                    ) : (
                      <div className="space-y-1 rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-300">
                        {evaluation.warnings.map((w, i) => (
                          <div key={i} className="flex items-start gap-1.5">
                            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                            <span>{w}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {evaluation.recommendations.length > 0 && (
                      <div className="space-y-1.5 rounded-xl border border-sky-500/30 bg-sky-500/10 p-3 text-[11px] text-sky-200">
                        <div className="font-bold flex items-center gap-1 text-sky-400">
                          <Sparkles className="h-3.5 w-3.5" /> Recommandations d&apos;installation :
                        </div>
                        {evaluation.recommendations.map((rec, i) => (
                          <div key={i}>• {rec}</div>
                        ))}
                      </div>
                    )}

                    <div className="border-t border-slate-800 pt-3 flex items-baseline justify-between">
                      <span className="text-xs font-semibold text-slate-400">Total Estimé du Kit</span>
                      <span className="text-2xl font-extrabold text-white">
                        {formatMoney(evaluation.package_total)}
                      </span>
                    </div>

                    <button
                      onClick={addKitToCart}
                      className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 text-xs font-extrabold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-500"
                    >
                      <ShoppingCart className="h-4 w-4" />
                      Ajouter tout le Kit au Panier
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

