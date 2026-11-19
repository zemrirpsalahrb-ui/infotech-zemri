"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Shield,
  ShoppingCart,
  User,
  Search,
  Layers,
  Cpu,
  LayoutDashboard,
  Menu,
  X,
  LogOut,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { useStore } from "@/context/StoreContext";
import { formatMoney } from "@/lib/api";

export default function Navbar() {
  const { profile, logout, cartCount, cartTotal, compareList } = useStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/catalog?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      router.push("/catalog");
    }
  };

  const tierLabel = () => {
    if (!profile) return null;
    if (profile.is_admin) return { text: "ADMINISTRATION", color: "bg-blue-600/20 text-blue-400 border-blue-500/40" };
    if (profile.effective_tier === "RESELLER")
      return { text: "TARIF REVENDEUR GROS", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40" };
    if (profile.effective_tier === "INSTALLER")
      return { text: "TARIF INSTALLATEUR PRO", color: "bg-sky-500/20 text-sky-400 border-sky-500/40" };
    if (profile.approval_status === "PENDING")
      return { text: `PRO EN ATTENTE (${profile.requested_type})`, color: "bg-amber-500/20 text-amber-400 border-amber-500/40" };
    return { text: "CLIENT PUBLIC", color: "bg-slate-800 text-slate-300 border-slate-700" };
  };

  const badge = tierLabel();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-[#07090E]/90 backdrop-blur-xl">
      {/* Top status bar */}
      <div className="border-b border-slate-900 bg-[#05070B] px-4 py-1.5 text-xs text-slate-400">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-blue-400 font-medium">
              <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
              Système CCTV & Sécurité Synchronisé en Direct
            </span>
            <span className="hidden md:inline text-slate-500">|</span>
            <span className="hidden md:inline">Livraison 58 Wilayas & Retrait Magasin</span>
          </div>
          <div className="flex items-center gap-3">
            {badge && (
              <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${badge.color}`}>
                {profile?.approval_status === "PENDING" ? <Clock className="h-3 w-3" /> : <CheckCircle2 className="h-3 w-3" />}
                {badge.text}
              </span>
            )}
            <Link href="/account" className="hover:text-white transition-colors">
              Espace Installateurs & Revendeurs
            </Link>
          </div>
        </div>
      </div>

      {/* Main Navigation */}
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3.5">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-sky-500 shadow-lg shadow-blue-600/25 group-hover:scale-105 transition-transform">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-extrabold tracking-tight text-white">
              LOGI<span className="text-blue-500">SZ</span>
            </span>
            <span className="block text-[10px] font-semibold uppercase tracking-widest text-slate-400">
              CCTV & Security Systems
            </span>
          </div>
        </Link>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="hidden flex-1 max-w-md lg:flex">
          <div className="relative w-full">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Rechercher caméra, XVR, NVR, disque WD Purple, référence..."
              className="w-full rounded-xl border border-slate-800 bg-[#0F1420] py-2.5 pl-4 pr-10 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
            <button
              type="submit"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-400"
            >
              <Search className="h-4 w-4" />
            </button>
          </div>
        </form>

        {/* Desktop Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
          <Link href="/catalog" className="hover:text-blue-400 transition-colors">
            Catalogue
          </Link>
          <Link
            href="/kit-builder"
            className="flex items-center gap-1.5 text-sky-400 hover:text-sky-300 font-semibold transition-colors"
          >
            <Cpu className="h-4 w-4" />
            Kit Builder CCTV
          </Link>
          {compareList.length > 0 && (
            <Link
              href="/catalog?compare=1"
              className="flex items-center gap-1 rounded-lg border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 text-xs text-blue-400"
            >
              <Layers className="h-3.5 w-3.5" />
              Comparer ({compareList.length})
            </Link>
          )}
          {profile?.is_admin && (
            <Link
              href="/admin"
              className="flex items-center gap-1.5 rounded-lg border border-blue-500/40 bg-blue-600/15 px-3 py-1.5 text-xs font-semibold text-blue-300 hover:bg-blue-600/25"
            >
              <LayoutDashboard className="h-4 w-4" />
              Admin Web
            </Link>
          )}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {profile ? (
            <div className="flex items-center gap-2">
              <Link
                href="/account"
                className="flex items-center gap-2 rounded-xl border border-slate-800 bg-[#0F1420] px-3 py-2 text-xs font-medium text-slate-200 hover:border-slate-700"
              >
                <User className="h-4 w-4 text-blue-400" />
                <span className="hidden sm:inline">{profile.username}</span>
              </Link>
              <button
                onClick={logout}
                title="Déconnexion"
                className="rounded-xl border border-slate-800 bg-[#0F1420] p-2 text-slate-400 hover:text-red-400"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/account"
              className="flex items-center gap-2 rounded-xl border border-slate-800 bg-[#0F1420] px-3.5 py-2 text-xs font-semibold text-slate-200 hover:border-blue-500/50"
            >
              <User className="h-4 w-4 text-blue-400" />
              <span>Connexion / Pro</span>
            </Link>
          )}

          <Link
            href="/cart"
            className="flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-sky-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-blue-600/20 hover:from-blue-500 hover:to-sky-500 transition-all"
          >
            <div className="relative">
              <ShoppingCart className="h-4 w-4" />
              {cartCount > 0 && (
                <span className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-white text-[10px] font-extrabold text-blue-700">
                  {cartCount}
                </span>
              )}
            </div>
            <span className="hidden sm:inline">{formatMoney(cartTotal)}</span>
          </Link>

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden rounded-lg border border-slate-800 p-2 text-slate-300"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="border-t border-slate-800 bg-[#0B0F19] px-4 py-4 md:hidden space-y-3">
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Rechercher un produit CCTV..."
              className="flex-1 rounded-lg border border-slate-800 bg-[#07090E] px-3 py-2 text-sm text-white"
            />
            <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-bold text-white">
              OK
            </button>
          </form>
          <div className="flex flex-col gap-2 text-sm text-slate-300">
            <Link href="/catalog" onClick={() => setMobileOpen(false)} className="py-1.5 hover:text-blue-400">
              Catalogue Produits
            </Link>
            <Link href="/kit-builder" onClick={() => setMobileOpen(false)} className="py-1.5 text-sky-400 font-semibold">
              Configurateur de Kit CCTV
            </Link>
            <Link href="/account" onClick={() => setMobileOpen(false)} className="py-1.5 hover:text-blue-400">
              Mon Compte (Installateur / Revendeur)
            </Link>
            {profile?.is_admin && (
              <Link href="/admin" onClick={() => setMobileOpen(false)} className="py-1.5 text-blue-400 font-bold">
                Administration du Site
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}

