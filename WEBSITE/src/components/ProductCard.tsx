"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ShoppingCart, Star, Layers, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { Product } from "@/types";
import { formatMoney } from "@/lib/api";
import { useStore } from "@/context/StoreContext";

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=800&q=80";

export default function ProductCard({ product }: { product: Product }) {
  const { addToCart, compareList, toggleCompare } = useStore();
  const isCompared = compareList.some((p) => p.id === product.id);
  const hasDiscount = product.effective_price < product.public_price;

  return (
    <motion.div
      whileHover={{ y: -5 }}
      transition={{ duration: 0.2 }}
      className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-800/90 bg-[#0F1420] p-4 shadow-xl transition-all hover:border-blue-500/50 hover:shadow-blue-950/30"
    >
      {/* Top badges */}
      <div>
        <div className="relative mb-3.5 aspect-[4/3] w-full overflow-hidden rounded-xl bg-[#07090E]">
          <Link href={`/product/${product.slug || product.reference}`}>
            <img
              src={product.main_image || FALLBACK_IMAGE}
              alt={product.name}
              className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-105"
            />
          </Link>

          <div className="absolute left-2.5 top-2.5 flex flex-wrap gap-1.5">
            {product.applied_tier !== "PUBLIC" && (
              <span className="rounded-md bg-blue-600/90 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white backdrop-blur-md">
                Tarif {product.applied_tier}
              </span>
            )}
            {product.is_special_offer || product.promo_price ? (
              <span className="rounded-md bg-rose-600/90 px-2 py-0.5 text-[10px] font-bold uppercase text-white">
                Promo
              </span>
            ) : null}
          </div>

          <button
            onClick={() => toggleCompare(product)}
            title="Comparer ce produit"
            className={`absolute right-2.5 top-2.5 rounded-lg p-1.5 text-xs backdrop-blur-md transition-colors ${
              isCompared
                ? "bg-blue-600 text-white"
                : "bg-slate-900/80 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <Layers className="h-4 w-4" />
          </button>
        </div>

        {/* Meta */}
        <div className="mb-1 flex items-center justify-between text-[11px] text-slate-400">
          <span className="font-mono text-blue-400">Réf: {product.reference}</span>
          <span className="font-semibold uppercase text-slate-400">{product.brand_name}</span>
        </div>

        <Link
          href={`/product/${product.slug || product.reference}`}
          className="line-clamp-2 text-sm font-bold text-white group-hover:text-blue-400 transition-colors"
        >
          {product.name}
        </Link>

        <p className="mt-1.5 line-clamp-2 text-xs text-slate-400">
          {product.short_description || `Équipement professionnel ${product.category_name}`}
        </p>
      </div>

      {/* Bottom Pricing & CTA */}
      <div className="mt-4 pt-3 border-t border-slate-800/70">
        <div className="mb-2.5 flex items-center justify-between">
          <div className="flex items-center gap-1 text-xs text-amber-400">
            <Star className="h-3.5 w-3.5 fill-amber-400" />
            <span className="font-semibold text-slate-200">{product.avg_rating}</span>
            <span className="text-slate-500">({product.review_count})</span>
          </div>

          {product.in_stock ? (
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              En stock ({product.available_stock})
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              Sur commande
            </span>
          )}
        </div>

        <div className="flex items-end justify-between gap-2">
          <div>
            {hasDiscount && (
              <span className="block text-xs text-slate-500 line-through">
                {formatMoney(product.public_price)}
              </span>
            )}
            <span className="text-lg font-extrabold text-white">
              {formatMoney(product.effective_price)}
            </span>
          </div>

          <button
            onClick={() => addToCart(product, 1)}
            className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-3.5 py-2 text-xs font-bold text-white shadow-md shadow-blue-600/20 hover:bg-blue-500 active:scale-95 transition-all"
          >
            <ShoppingCart className="h-3.5 w-3.5" />
            Ajouter
          </button>
        </div>

        <div className="mt-2 flex items-center gap-1 text-[10px] text-slate-500">
          <ShieldCheck className="h-3 w-3 text-blue-400" />
          <span>Garantie {product.warranty_months || 12} mois</span>
        </div>
      </div>
    </motion.div>
  );
}

