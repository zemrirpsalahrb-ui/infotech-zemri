"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  LayoutDashboard,
  ShoppingBag,
  Users,
  Package,
  MessageSquare,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Image as ImageIcon,
  Plus,
} from "lucide-react";
import { apiFetch, formatMoney } from "@/lib/api";
import { CustomerProfile, OnlineOrder, Product, Review } from "@/types";
import { useStore } from "@/context/StoreContext";

export default function AdminDashboardPage() {
  const { profile } = useStore();
  const [activeTab, setActiveTab] = useState<
    "overview" | "orders" | "accounts" | "products" | "reviews"
  >("overview");

  const [stats, setStats] = useState<any>(null);
  const [orders, setOrders] = useState<OnlineOrder[]>([]);
  const [accounts, setAccounts] = useState<CustomerProfile[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [statusMsg, setStatusMsg] = useState("");

  // Product edit & gallery modal state
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [editDesc, setEditDesc] = useState("");
  const [editShortDesc, setEditShortDesc] = useState("");
  const [editPromoPrice, setEditPromoPrice] = useState("");
  const [editInstallerPrice, setEditInstallerPrice] = useState("");
  const [newImageUrl, setNewImageUrl] = useState("");

  const loadAll = async () => {
    try {
      const dash = await apiFetch("/admin/dashboard/");
      setStats(dash);
      const ordRes = await apiFetch<{ orders: OnlineOrder[] }>("/desktop/orders/");
      setOrders(ordRes.orders || []);
      const accRes = await apiFetch<CustomerProfile[]>("/admin/accounts/");
      setAccounts(accRes || []);
      const prodRes = await apiFetch<Product[]>("/admin/products/");
      setProducts(prodRes || []);
      const revRes = await apiFetch<Review[]>("/admin/reviews/");
      setReviews(revRes || []);
    } catch {
      // ignore if not logged in as admin yet
    }
  };

  useEffect(() => {
    loadAll();
  }, [profile]);

  const updateOrderStatus = async (orderUid: string, newStatus: string) => {
    try {
      await apiFetch(`/desktop/orders/${orderUid}/status/`, {
        method: "POST",
        body: JSON.stringify({ status: newStatus }),
      });
      setStatusMsg(`Statut de la commande ${orderUid} passé à ${newStatus}`);
      loadAll();
    } catch (e: any) {
      setStatusMsg(e.message);
    }
  };

  const moderateAccount = async (profileId: number, action: string, accountType?: string) => {
    try {
      await apiFetch(`/admin/accounts/${profileId}/moderate/`, {
        method: "POST",
        body: JSON.stringify({ action, account_type: accountType }),
      });
      setStatusMsg("Compte client mis à jour.");
      loadAll();
    } catch (e: any) {
      setStatusMsg(e.message);
    }
  };

  const moderateReview = async (reviewId: number, action: string, reply?: string) => {
    try {
      await apiFetch(`/admin/reviews/${reviewId}/moderate/`, {
        method: "POST",
        body: JSON.stringify({ action, ...(reply !== undefined ? { admin_reply: reply } : {}) }),
      });
      setStatusMsg("Avis mis à jour.");
      loadAll();
    } catch (e: any) {
      setStatusMsg(e.message);
    }
  };

  const saveProductContent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    try {
      await apiFetch(`/admin/products/${editingProduct.id}/`, {
        method: "PUT",
        body: JSON.stringify({
          short_description: editShortDesc,
          description: editDesc,
          promo_price: editPromoPrice ? Number(editPromoPrice) : null,
          installer_price: editInstallerPrice ? Number(editInstallerPrice) : editingProduct.public_price,
        }),
      });
      setStatusMsg(`Produit ${editingProduct.reference} enrichi avec succès.`);
      setEditingProduct(null);
      loadAll();
    } catch (err: any) {
      setStatusMsg(err.message);
    }
  };

  const addProductImage = async () => {
    if (!editingProduct || !newImageUrl.trim()) return;
    try {
      await apiFetch(`/admin/products/${editingProduct.id}/images/`, {
        method: "POST",
        body: JSON.stringify({ image_url: newImageUrl.trim(), is_main: true }),
      });
      setNewImageUrl("");
      setStatusMsg("Image ajoutée à la galerie Cloudinary/Externe.");
      loadAll();
    } catch (err: any) {
      setStatusMsg(err.message);
    }
  };

  if (!profile || !profile.is_admin) {
    return (
      <div className="mx-auto max-w-xl px-4 py-20 text-center space-y-4">
        <h1 className="text-2xl font-extrabold text-white">Accès Réservé à l&apos;Administrateur</h1>
        <p className="text-xs text-slate-400">
          Veuillez vous connecter avec le compte administrateur (<code className="text-blue-400">admin</code> / <code className="text-blue-400">admin123</code>) pour gérer la boutique.
        </p>
        <Link href="/account" className="inline-block rounded-xl bg-blue-600 px-6 py-3 text-xs font-bold text-white">
          Aller à la page de connexion
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 space-y-8">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-blue-400">
            Back-Office Central • Neon & Desktop Sync
          </span>
          <h1 className="text-2xl font-extrabold text-white">
            Administration de la Boutique CCTV
          </h1>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            { id: "overview", label: "Vue d'ensemble", icon: LayoutDashboard },
            { id: "orders", label: `Commandes (${orders.length})`, icon: ShoppingBag },
            { id: "accounts", label: `Comptes Pro (${accounts.length})`, icon: Users },
            { id: "products", label: `Produits & Images (${products.length})`, icon: Package },
            { id: "reviews", label: `Avis (${reviews.length})`, icon: MessageSquare },
          ].map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                  activeTab === t.id
                    ? "bg-blue-600 text-white"
                    : "border border-slate-800 bg-[#0F1420] text-slate-300"
                }`}
              >
                <Icon className="h-4 w-4" />
                {t.label}
              </button>
            );
          })}
          <button
            onClick={loadAll}
            className="rounded-xl border border-slate-700 bg-slate-800 p-2 text-slate-200 hover:text-white"
            title="Rafraîchir"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className="rounded-xl border border-blue-500/40 bg-blue-500/10 px-4 py-2.5 text-xs font-semibold text-blue-300">
          {statusMsg}
        </div>
      )}

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && stats && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-5">
              <span className="text-xs text-slate-400">Chiffre Commandes Web</span>
              <div className="mt-1 text-xl font-extrabold text-emerald-400">
                {formatMoney(stats.kpis.total_online_revenue)}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-5">
              <span className="text-xs text-slate-400">Commandes en attente</span>
              <div className="mt-1 text-xl font-extrabold text-blue-400">
                {stats.kpis.new_orders} / {stats.kpis.total_orders}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-5">
              <span className="text-xs text-slate-400">Demandes Pro en attente</span>
              <div className="mt-1 text-xl font-extrabold text-amber-400">
                {stats.kpis.pending_installers + stats.kpis.pending_resellers}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-5">
              <span className="text-xs text-slate-400">Conflits de Stock détectés</span>
              <div className="mt-1 text-xl font-extrabold text-rose-400">
                {stats.kpis.conflict_orders}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-6 space-y-4">
            <h2 className="text-base font-bold text-white">Journal de Synchronisation Desktop ↔ Web</h2>
            <div className="space-y-2 text-xs">
              {(stats.recent_sync_logs || []).map((log: any) => (
                <div
                  key={log.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-800 bg-[#07090E] p-3"
                >
                  <div>
                    <span className="font-mono text-blue-400">[{log.event_type}]</span>{" "}
                    <span className="text-slate-200">{log.summary}</span>
                  </div>
                  <span
                    className={`font-bold ${
                      log.status === "SUCCESS" ? "text-emerald-400" : "text-amber-400"
                    }`}
                  >
                    {log.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ONLINE ORDERS */}
      {activeTab === "orders" && (
        <div className="space-y-4">
          {orders.map((o) => (
            <div
              key={o.id}
              className="rounded-2xl border border-slate-800 bg-[#0F1420] p-5 space-y-3 text-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                  <span className="font-mono text-sm font-extrabold text-blue-400">
                    {o.order_uid}
                  </span>
                  <span className="ml-3 font-bold text-white">{o.customer_name}</span>
                  <span className="ml-2 text-slate-400">({o.customer_phone} • {o.wilaya})</span>
                </div>
                <div className="flex items-center gap-2">
                  {o.pos_converted && (
                    <span className="rounded-lg bg-emerald-500/20 px-2.5 py-1 font-bold text-emerald-300">
                      Convertie POS Bon N° {o.pos_bon_number}
                    </span>
                  )}
                  <select
                    value={o.status}
                    onChange={(e) => updateOrderStatus(o.order_uid, e.target.value)}
                    className="rounded-xl border border-slate-700 bg-[#07090E] px-3 py-1.5 font-bold text-white"
                  >
                    {[
                      "NEW",
                      "PENDING",
                      "CONFIRMED",
                      "PREPARING",
                      "READY_FOR_PICKUP",
                      "SHIPPED",
                      "DELIVERED",
                      "CANCELLED",
                      "REJECTED",
                    ].map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {o.has_stock_conflict && (
                <div className="flex items-center gap-2 rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-rose-300 font-semibold">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>Conflit de stock : {o.conflict_details}</span>
                </div>
              )}

              <div className="space-y-1">
                {o.items.map((it) => (
                  <div key={it.id} className="flex justify-between text-slate-300">
                    <span>
                      {it.quantity} × [{it.product_reference}] {it.product_name}
                    </span>
                    <span className="font-bold text-white">{formatMoney(it.line_total)}</span>
                  </div>
                ))}
              </div>

              <div className="flex justify-between border-t border-slate-800 pt-2 font-extrabold text-white">
                <span>
                  {o.delivery_method} • {o.payment_method} • Tarif {o.applied_tier}
                </span>
                <span className="text-sm text-emerald-400">{formatMoney(o.total_amount)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 3: INSTALLER & RESELLER ACCOUNTS */}
      {activeTab === "accounts" && (
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-[#0F1420]">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-[#07090E] text-slate-400">
              <tr>
                <th className="p-3.5">Utilisateur / Société</th>
                <th className="p-3.5">Téléphone & RC/NIF</th>
                <th className="p-3.5">Profil Demandé</th>
                <th className="p-3.5">Statut</th>
                <th className="p-3.5">Tarif Effectif</th>
                <th className="p-3.5">Actions Administrateur</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {accounts.map((acc) => (
                <tr key={acc.id}>
                  <td className="p-3.5">
                    <div className="font-bold text-white">{acc.username}</div>
                    <div className="text-slate-400">{acc.company_name || acc.email}</div>
                  </td>
                  <td className="p-3.5 text-slate-300">
                    <div>{acc.phone}</div>
                    {acc.rc_number && <div className="text-[11px] text-slate-500">RC: {acc.rc_number}</div>}
                  </td>
                  <td className="p-3.5 font-bold text-sky-400">{acc.requested_type}</td>
                  <td className="p-3.5">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                        acc.approval_status === "APPROVED"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : acc.approval_status === "PENDING"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {acc.approval_status}
                    </span>
                  </td>
                  <td className="p-3.5 font-extrabold text-white">{acc.effective_tier}</td>
                  <td className="p-3.5 flex flex-wrap gap-1.5">
                    <button
                      onClick={() => moderateAccount(acc.id, "APPROVE", "INSTALLER")}
                      className="rounded-lg bg-sky-600 px-2.5 py-1 font-bold text-white hover:bg-sky-500"
                    >
                      Approuver Installateur
                    </button>
                    <button
                      onClick={() => moderateAccount(acc.id, "APPROVE", "RESELLER")}
                      className="rounded-lg bg-emerald-600 px-2.5 py-1 font-bold text-white hover:bg-emerald-500"
                    >
                      Approuver Revendeur
                    </button>
                    <button
                      onClick={() => moderateAccount(acc.id, "REJECT")}
                      className="rounded-lg bg-rose-600/30 border border-rose-500/40 px-2.5 py-1 font-bold text-rose-300"
                    >
                      Rejeter / Public
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 4: PRODUCTS & IMAGES */}
      {activeTab === "products" && (
        <div className="space-y-6">
          {editingProduct && (
            <form
              onSubmit={saveProductContent}
              className="rounded-3xl border border-blue-500/40 bg-[#0F1420] p-6 space-y-4"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-base font-extrabold text-white">
                  Éditer Contenu Web & Images : [{editingProduct.reference}] {editingProduct.name}
                </h3>
                <button
                  type="button"
                  onClick={() => setEditingProduct(null)}
                  className="text-xs text-slate-400 hover:text-white"
                >
                  Fermer
                </button>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs text-slate-400">Prix Installateur (DA)</label>
                  <input
                    type="number"
                    value={editInstallerPrice}
                    onChange={(e) => setEditInstallerPrice(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400">Prix Promotionnel (DA - optionnel)</label>
                  <input
                    type="number"
                    value={editPromoPrice}
                    onChange={(e) => setEditPromoPrice(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400">Résumé court</label>
                <input
                  type="text"
                  value={editShortDesc}
                  onChange={(e) => setEditShortDesc(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400">Description détaillée</label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] p-3 text-xs text-white"
                />
              </div>
              <div className="flex gap-2">
                <input
                  type="url"
                  placeholder="Ajouter URL d'image Cloudinary / Externe..."
                  value={newImageUrl}
                  onChange={(e) => setNewImageUrl(e.target.value)}
                  className="flex-1 rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                />
                <button
                  type="button"
                  onClick={addProductImage}
                  className="inline-flex items-center gap-1 rounded-xl bg-sky-600 px-4 py-2 text-xs font-bold text-white"
                >
                  <Plus className="h-3.5 w-3.5" /> Ajouter Image
                </button>
              </div>
              <button
                type="submit"
                className="rounded-xl bg-blue-600 px-6 py-2.5 text-xs font-extrabold text-white"
              >
                Enregistrer les modifications Web
              </button>
            </form>
          )}

          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-[#0F1420]">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 bg-[#07090E] text-slate-400">
                <tr>
                  <th className="p-3.5">Réf / IDE Desktop</th>
                  <th className="p-3.5">Produit</th>
                  <th className="p-3.5">Stock Physique / Réservé</th>
                  <th className="p-3.5">Prix Public / Gros</th>
                  <th className="p-3.5">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {products.map((p) => (
                  <tr key={p.id}>
                    <td className="p-3.5 font-mono text-blue-400">
                      {p.reference} <span className="text-slate-500">(#{p.desktop_ide || "—"})</span>
                    </td>
                    <td className="p-3.5 font-bold text-white">{p.name}</td>
                    <td className="p-3.5">
                      <span className="font-bold text-emerald-400">{p.physical_stock}</span>{" "}
                      <span className="text-slate-500">(rés: {p.reserved_stock})</span>
                    </td>
                    <td className="p-3.5 text-slate-200">
                      {formatMoney(p.public_price)} /{" "}
                      <span className="text-sky-400">{formatMoney(p.tier_prices?.reseller_price)}</span>
                    </td>
                    <td className="p-3.5">
                      <button
                        onClick={() => {
                          setEditingProduct(p);
                          setEditShortDesc(p.short_description || "");
                          setEditDesc(p.description || "");
                          setEditPromoPrice(p.promo_price ? String(p.promo_price) : "");
                          setEditInstallerPrice(
                            p.tier_prices?.installer_price ? String(p.tier_prices.installer_price) : ""
                          );
                        }}
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 font-bold text-white hover:border-blue-500"
                      >
                        <ImageIcon className="h-3.5 w-3.5 text-blue-400" /> Éditer Contenu & Images
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: REVIEWS MODERATION */}
      {activeTab === "reviews" && (
        <div className="space-y-3">
          {reviews.map((r) => (
            <div
              key={r.id}
              className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-800 bg-[#0F1420] p-4 text-xs sm:flex-row sm:items-center"
            >
              <div className="space-y-1">
                <div className="font-bold text-white">
                  {r.author_name} — {r.rating}/5 ★ sur{" "}
                  <span className="text-blue-400">{r.product_name}</span>
                </div>
                <p className="text-slate-300">{r.comment}</p>
                <span className="inline-block rounded bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">
                  Statut : {r.status}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => moderateReview(r.id, "APPROVED")}
                  className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 font-bold text-white"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" /> Approuver
                </button>
                <button
                  onClick={() => moderateReview(r.id, "HIDDEN")}
                  className="inline-flex items-center gap-1 rounded-lg bg-amber-600/30 px-3 py-1.5 font-bold text-amber-300"
                >
                  Masquer
                </button>
                <button
                  onClick={() => moderateReview(r.id, "DELETE")}
                  className="inline-flex items-center gap-1 rounded-lg bg-rose-600/30 px-3 py-1.5 font-bold text-rose-300"
                >
                  <XCircle className="h-3.5 w-3.5" /> Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

