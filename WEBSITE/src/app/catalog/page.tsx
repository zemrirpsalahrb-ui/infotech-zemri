"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Filter, Search, Layers, X, SlidersHorizontal, RotateCcw } from "lucide-react";
import { apiFetch, formatMoney } from "@/lib/api";
import { Brand, Category, Product } from "@/types";
import ProductCard from "@/components/ProductCard";
import { useStore } from "@/context/StoreContext";

function CatalogContent() {
  const searchParams = useSearchParams();
  const { compareList, toggleCompare, clearCompare, addToCart } = useStore();

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);

  const [q, setQ] = useState(searchParams.get("q") || "");
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get("category") || "all");
  const [selectedBrand, setSelectedBrand] = useState(searchParams.get("brand") || "all");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [inStockOnly, setInStockOnly] = useState(false);
  const [sortBy, setSortBy] = useState("newest");
  const [showCompareModal, setShowCompareModal] = useState(searchParams.get("compare") === "1");

  useEffect(() => {
    apiFetch<{ categories: Category[]; brands: Brand[] }>("/catalog/home/")
      .then((res) => {
        setCategories(res.categories || []);
        setBrands(res.brands || []);
      })
      .catch(() => {});
  }, []);

  const loadProducts = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (selectedCategory !== "all") params.set("category", selectedCategory);
    if (selectedBrand !== "all") params.set("brand", selectedBrand);
    if (minPrice) params.set("min_price", minPrice);
    if (maxPrice) params.set("max_price", maxPrice);
    if (inStockOnly) params.set("in_stock", "true");
    if (sortBy) params.set("sort", sortBy);

    apiFetch<{ results: Product[] }>(`/products/?${params.toString()}`)
      .then((res) => setProducts(res.results || []))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProducts();
  }, [selectedCategory, selectedBrand, inStockOnly, sortBy]);

  const resetFilters = () => {
    setQ("");
    setSelectedCategory("all");
    setSelectedBrand("all");
    setMinPrice("");
    setMaxPrice("");
    setInStockOnly(false);
    setSortBy("newest");
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      {/* Header */}
      <div className="mb-8 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 md:flex-row md:items-center">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-blue-400">
            Catalogue Professionnel CCTV
          </span>
          <h1 className="mt-1 text-3xl font-extrabold text-white">
            Tous nos Équipements de Sécurité ({products.length})
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {compareList.length > 0 && (
            <button
              onClick={() => setShowCompareModal(true)}
              className="flex items-center gap-2 rounded-xl bg-blue-600/20 border border-blue-500/40 px-4 py-2.5 text-xs font-bold text-blue-300 hover:bg-blue-600/30"
            >
              <Layers className="h-4 w-4" />
              Comparer ({compareList.length}/4)
            </button>
          )}

          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-xl border border-slate-800 bg-[#0F1420] px-3.5 py-2 text-xs font-semibold text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="newest">Plus récents</option>
              <option value="price_asc">Prix croissant</option>
              <option value="price_desc">Prix décroissant</option>
              <option value="name">Ordre alphabétique (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Sidebar Filters */}
        <aside className="lg:col-span-3 space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-5 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="flex items-center gap-2 text-sm font-bold text-white">
                <Filter className="h-4 w-4 text-blue-400" />
                Filtres Avancés
              </span>
              <button
                onClick={resetFilters}
                className="flex items-center gap-1 text-xs text-slate-400 hover:text-blue-400"
              >
                <RotateCcw className="h-3 w-3" /> Réinitialiser
              </button>
            </div>

            {/* Search */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                loadProducts();
              }}
              className="space-y-2"
            >
              <label className="text-xs font-semibold text-slate-300">Recherche rapide</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Nom, réf, modèle..."
                  className="w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
                />
                <button
                  type="submit"
                  className="rounded-xl bg-blue-600 px-3 py-2 text-white hover:bg-blue-500"
                >
                  <Search className="h-4 w-4" />
                </button>
              </div>
            </form>

            {/* Category filter */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Catégorie CCTV</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2.5 text-xs text-white focus:border-blue-500 focus:outline-none"
              >
                <option value="all">Toutes les catégories</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.slug}>
                    {c.name} ({c.product_count})
                  </option>
                ))}
              </select>
            </div>

            {/* Brand filter */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Marque</label>
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2.5 text-xs text-white focus:border-blue-500 focus:outline-none"
              >
                <option value="all">Toutes les marques</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.slug}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Price filter */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Budget (DA)</label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  placeholder="Min DA"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                />
                <input
                  type="number"
                  placeholder="Max DA"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                />
              </div>
              <button
                onClick={loadProducts}
                className="w-full rounded-xl border border-slate-700 bg-slate-800/60 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-800"
              >
                Appliquer le prix
              </button>
            </div>

            {/* Availability filter */}
            <label className="flex cursor-pointer items-center gap-2.5 pt-2 text-xs font-medium text-slate-200">
              <input
                type="checkbox"
                checked={inStockOnly}
                onChange={(e) => setInStockOnly(e.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-blue-600"
              />
              <span>En stock uniquement</span>
            </label>
          </div>
        </aside>

        {/* Product Grid */}
        <div className="lg:col-span-9">
          {loading ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <div key={n} className="h-80 animate-pulse rounded-2xl border border-slate-800 bg-[#0F1420]" />
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-12 text-center space-y-3">
              <p className="text-lg font-bold text-white">Aucun produit ne correspond à vos critères.</p>
              <p className="text-xs text-slate-400">Essayez d&apos;élargir votre recherche ou de réinitialiser les filtres.</p>
              <button
                onClick={resetFilters}
                className="mt-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white"
              >
                Afficher tout le catalogue
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {products.map((prod) => (
                <ProductCard key={prod.id} product={prod} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Product Comparison Modal */}
      {showCompareModal && compareList.length > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-5xl overflow-auto rounded-3xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl">
            <div className="mb-6 flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-xl font-extrabold text-white">Comparateur Technique CCTV</h2>
                <p className="text-xs text-slate-400">Comparez les caractéristiques et tarifs de vos équipements</p>
              </div>
              <div className="flex items-center gap-3">
                <button onClick={clearCompare} className="text-xs text-rose-400 hover:underline">
                  Tout vider
                </button>
                <button
                  onClick={() => setShowCompareModal(false)}
                  className="rounded-xl border border-slate-800 p-2 text-slate-400 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="p-3 text-slate-400 w-40">Caractéristique</th>
                    {compareList.map((p) => (
                      <th key={p.id} className="p-3 min-w-[200px] text-white font-bold">
                        <div className="flex items-start justify-between gap-2">
                          <span>{p.name}</span>
                          <button onClick={() => toggleCompare(p)} className="text-slate-500 hover:text-rose-400">
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70">
                  <tr>
                    <td className="p-3 font-semibold text-slate-400">Référence</td>
                    {compareList.map((p) => (
                      <td key={p.id} className="p-3 font-mono text-blue-400">{p.reference}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-400">Marque</td>
                    {compareList.map((p) => (
                      <td key={p.id} className="p-3 text-slate-200">{p.brand_name}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-400">Votre Tarif</td>
                    {compareList.map((p) => (
                      <td key={p.id} className="p-3 text-base font-extrabold text-emerald-400">
                        {formatMoney(p.effective_price)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-400">Disponibilité</td>
                    {compareList.map((p) => (
                      <td key={p.id} className="p-3 text-slate-200">
                        {p.in_stock ? `En stock (${p.available_stock})` : "Sur commande"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-400">Garantie</td>
                    {compareList.map((p) => (
                      <td key={p.id} className="p-3 text-slate-200">{p.warranty_months} mois</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-400">Spécifications</td>
                    {compareList.map((p) => (
                      <td key={p.id} className="p-3 text-slate-300 space-y-1">
                        {Object.entries(p.technical_specs || {}).map(([k, v]) => (
                          <div key={k}>
                            <span className="text-slate-500">{k}:</span> {v}
                          </div>
                        ))}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3"></td>
                    {compareList.map((p) => (
                      <td key={p.id} className="p-3">
                        <button
                          onClick={() => addToCart(p, 1)}
                          className="w-full rounded-xl bg-blue-600 py-2 font-bold text-white hover:bg-blue-500"
                        >
                          Ajouter au panier
                        </button>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CatalogPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-slate-400">Chargement du catalogue...</div>}>
      <CatalogContent />
    </Suspense>
  );
}

