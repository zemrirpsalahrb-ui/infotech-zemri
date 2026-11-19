"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Trash2,
  ShoppingBag,
  Truck,
  Store,
  CheckCircle2,
  MessageCircle,
  Search,
  AlertTriangle,
} from "lucide-react";
import { useStore } from "@/context/StoreContext";
import { apiFetch, buildWhatsAppLink, formatMoney } from "@/lib/api";
import { OnlineOrder } from "@/types";

export default function CartCheckoutPage() {
  const { cart, updateCartQty, removeFromCart, clearCart, cartTotal, profile } = useStore();

  const [customerName, setCustomerName] = useState(
    profile ? `${profile.first_name} ${profile.last_name}`.trim() || profile.username : ""
  );
  const [customerPhone, setCustomerPhone] = useState(profile?.phone || "");
  const [customerEmail, setCustomerEmail] = useState(profile?.email || "");
  const [companyName, setCompanyName] = useState(profile?.company_name || "");
  const [wilaya, setWilaya] = useState(profile?.wilaya || "Alger");
  const [deliveryAddress, setDeliveryAddress] = useState(profile?.address || "");
  const [deliveryMethod, setDeliveryMethod] = useState<"DELIVERY" | "PICKUP">("DELIVERY");
  const [paymentMethod, setPaymentMethod] = useState<
    "CASH_ON_DELIVERY" | "PAY_AT_STORE" | "BANK_TRANSFER" | "CIB_EDAHABIA"
  >("CASH_ON_DELIVERY");
  const [notes, setNotes] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [confirmedOrder, setConfirmedOrder] = useState<OnlineOrder | null>(null);
  const [whatsappNum, setWhatsappNum] = useState("+213550000000");

  // Order tracking
  const [trackUid, setTrackUid] = useState("");
  const [trackedOrder, setTrackedOrder] = useState<OnlineOrder | null>(null);
  const [trackError, setTrackError] = useState("");

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cart.length === 0) return;
    setSubmitting(true);
    setError("");
    const idempotencyKey = `WEB-CHK-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

    try {
      const res = await apiFetch<{ order: OnlineOrder; whatsapp_number: string }>("/orders/checkout/", {
        method: "POST",
        headers: { "X-Idempotency-Key": idempotencyKey },
        body: JSON.stringify({
          idempotency_key: idempotencyKey,
          customer_name: customerName,
          customer_phone: customerPhone,
          customer_email: customerEmail,
          company_name: companyName,
          wilaya,
          delivery_address: deliveryAddress,
          delivery_method: deliveryMethod,
          payment_method: paymentMethod,
          notes,
          items: cart.map((i) => ({
            product_id: i.product.id,
            reference: i.product.reference,
            quantity: i.quantity,
          })),
        }),
      });
      setConfirmedOrder(res.order);
      if (res.whatsapp_number) setWhatsappNum(res.whatsapp_number);
      clearCart();
    } catch (err: any) {
      setError(err.message || "Erreur lors de la validation de la commande.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleTrackOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trackUid.trim()) return;
    setTrackError("");
    setTrackedOrder(null);
    try {
      const res = await apiFetch<{ order: OnlineOrder }>(
        `/orders/track/${encodeURIComponent(trackUid.trim())}/`
      );
      setTrackedOrder(res.order);
    } catch (err: any) {
      setTrackError(err.message || "Commande introuvable.");
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 space-y-14">
      {/* Order Confirmation View */}
      {confirmedOrder ? (
        <div className="mx-auto max-w-3xl rounded-3xl border border-emerald-500/40 bg-[#0F1420] p-8 text-center space-y-6 shadow-2xl">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="h-10 w-10" />
          </div>
          <h1 className="text-2xl font-extrabold text-white sm:text-3xl">
            Commande Confirmée : {confirmedOrder.order_uid}
          </h1>
          <p className="text-sm text-slate-300">
            Merci <b>{confirmedOrder.customer_name}</b> ! Votre commande a été transmise à notre logiciel de gestion central LOGISZ.
          </p>

          {confirmedOrder.has_stock_conflict && (
            <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-xs text-amber-300 text-left">
              <div className="font-bold flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4" /> Vérification de disponibilité en cours :
              </div>
              <p className="mt-1">{confirmedOrder.conflict_details}</p>
            </div>
          )}

          <div className="rounded-2xl border border-slate-800 bg-[#07090E] p-5 text-left text-xs space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Numéro de commande :</span>
              <span className="font-mono font-bold text-blue-400">{confirmedOrder.order_uid}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Grille tarifaire appliquée :</span>
              <span className="font-bold text-white">{confirmedOrder.applied_tier}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Mode de réception :</span>
              <span className="text-white">{confirmedOrder.delivery_method}</span>
            </div>
            <div className="flex justify-between border-t border-slate-800 pt-2 text-sm font-extrabold text-emerald-400">
              <span>Total à payer :</span>
              <span>{formatMoney(confirmedOrder.total_amount)}</span>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-4 pt-2">
            <a
              href={buildWhatsAppLink(
                whatsappNum,
                `Bonjour LOGISZ, je viens de valider la commande en ligne N° ${confirmedOrder.order_uid} d'un montant de ${formatMoney(confirmedOrder.total_amount)} (${confirmedOrder.customer_name}).`
              )}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-xs font-bold text-white hover:bg-emerald-500"
            >
              <MessageCircle className="h-4 w-4" />
              Envoyer ma confirmation sur WhatsApp
            </a>
            <Link
              href="/catalog"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-6 py-3 text-xs font-bold text-white"
            >
              Continuer mes achats
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
          {/* Left: Cart Items */}
          <div className="lg:col-span-7 space-y-4">
            <h1 className="text-2xl font-extrabold text-white">
              Votre Panier ({cart.length} article{cart.length > 1 ? "s" : ""})
            </h1>

            {cart.length === 0 ? (
              <div className="rounded-3xl border border-slate-800 bg-[#0F1420] p-12 text-center space-y-4">
                <ShoppingBag className="mx-auto h-12 w-12 text-slate-500" />
                <p className="text-base font-bold text-white">Votre panier est vide</p>
                <p className="text-xs text-slate-400">
                  Parcourez notre catalogue CCTV ou utilisez le configurateur de kit.
                </p>
                <Link
                  href="/catalog"
                  className="inline-block rounded-xl bg-blue-600 px-6 py-3 text-xs font-bold text-white"
                >
                  Découvrir les produits
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {cart.map(({ product, quantity }) => (
                  <div
                    key={product.id}
                    className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-800 bg-[#0F1420] p-4 sm:flex-row sm:items-center"
                  >
                    <div className="space-y-1">
                      <span className="font-mono text-[11px] text-blue-400">
                        Réf: {product.reference}
                      </span>
                      <Link
                        href={`/product/${product.slug || product.reference}`}
                        className="block text-sm font-bold text-white hover:text-blue-400"
                      >
                        {product.name}
                      </Link>
                      <div className="text-xs text-slate-400">
                        Prix unitaire ({product.applied_tier}) :{" "}
                        <span className="font-bold text-white">
                          {formatMoney(product.effective_price)}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between gap-4 sm:justify-end">
                      <div className="flex items-center rounded-xl border border-slate-800 bg-[#07090E]">
                        <button
                          onClick={() => updateCartQty(product.id, quantity - 1)}
                          className="px-3 py-1.5 text-xs font-bold text-slate-300"
                        >
                          -
                        </button>
                        <span className="px-3 text-xs font-bold text-white">{quantity}</span>
                        <button
                          onClick={() => updateCartQty(product.id, quantity + 1)}
                          className="px-3 py-1.5 text-xs font-bold text-slate-300"
                        >
                          +
                        </button>
                      </div>

                      <div className="w-28 text-right text-sm font-extrabold text-white">
                        {formatMoney(product.effective_price * quantity)}
                      </div>

                      <button
                        onClick={() => removeFromCart(product.id)}
                        className="text-slate-500 hover:text-rose-400"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right: Checkout Form */}
          <div className="lg:col-span-5">
            <form
              onSubmit={handleCheckout}
              className="rounded-3xl border border-slate-800 bg-[#0F1420] p-6 space-y-4"
            >
              <h2 className="text-lg font-extrabold text-white border-b border-slate-800 pb-3">
                Validation de la Commande
              </h2>

              {!profile && (
                <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-3 text-xs text-blue-200">
                  Commande rapide en tant qu&apos;invité activée, ou{" "}
                  <Link href="/account" className="font-bold underline text-white">
                    connectez-vous à votre compte Pro
                  </Link>
                  .
                </div>
              )}

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Nom complet *</label>
                  <input
                    type="text"
                    required
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder="Ex: Mohamed Amine"
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Téléphone *</label>
                  <input
                    type="text"
                    required
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    placeholder="Ex: 0550 12 34 56"
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Entreprise (optionnel)</label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Nom de la société"
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Wilaya</label>
                  <input
                    type="text"
                    value={wilaya}
                    onChange={(e) => setWilaya(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                  />
                </div>
              </div>

              {/* Delivery vs Store Pickup */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300">Mode de réception</label>
                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setDeliveryMethod("DELIVERY")}
                    className={`flex items-center justify-center gap-2 rounded-xl border p-2.5 text-xs font-bold ${
                      deliveryMethod === "DELIVERY"
                        ? "border-blue-500 bg-blue-600/20 text-white"
                        : "border-slate-800 bg-[#07090E] text-slate-400"
                    }`}
                  >
                    <Truck className="h-4 w-4" /> Livraison
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeliveryMethod("PICKUP")}
                    className={`flex items-center justify-center gap-2 rounded-xl border p-2.5 text-xs font-bold ${
                      deliveryMethod === "PICKUP"
                        ? "border-blue-500 bg-blue-600/20 text-white"
                        : "border-slate-800 bg-[#07090E] text-slate-400"
                    }`}
                  >
                    <Store className="h-4 w-4" /> Retrait Magasin
                  </button>
                </div>
              </div>

              {deliveryMethod === "DELIVERY" && (
                <div>
                  <label className="text-xs font-semibold text-slate-300">Adresse de livraison</label>
                  <input
                    type="text"
                    required
                    value={deliveryAddress}
                    onChange={(e) => setDeliveryAddress(e.target.value)}
                    placeholder="Commune, rue, point de repère..."
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
                  />
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-300">Mode de règlement</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value as any)}
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2.5 text-xs text-white"
                >
                  <option value="CASH_ON_DELIVERY">Paiement à la livraison (Espèces)</option>
                  <option value="PAY_AT_STORE">Paiement au comptoir du magasin</option>
                  <option value="BANK_TRANSFER">Virement Bancaire / CCP</option>
                  <option value="CIB_EDAHABIA">Carte CIB / Edahabia</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Notes ou instructions</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Précisions pour la préparation..."
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] p-2.5 text-xs text-white"
                />
              </div>

              {/* Totals */}
              <div className="border-t border-slate-800 pt-4 space-y-2 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Sous-total articles</span>
                  <span className="font-bold text-white">{formatMoney(cartTotal)}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Frais de livraison</span>
                  <span className="font-bold text-white">
                    {deliveryMethod === "PICKUP" || cartTotal >= 50000
                      ? "Gratuit (0,00 DA)"
                      : formatMoney(600)}
                  </span>
                </div>
                <div className="flex justify-between border-t border-slate-800 pt-2 text-base font-extrabold text-white">
                  <span>Total TTC</span>
                  <span className="text-blue-400">
                    {formatMoney(
                      cartTotal + (deliveryMethod === "PICKUP" || cartTotal >= 50000 ? 0 : 600)
                    )}
                  </span>
                </div>
              </div>

              {error && <p className="text-xs font-semibold text-rose-400">{error}</p>}

              <button
                type="submit"
                disabled={cart.length === 0 || submitting}
                className="w-full rounded-xl bg-blue-600 py-3.5 text-xs font-extrabold text-white shadow-xl shadow-blue-600/25 hover:bg-blue-500 disabled:opacity-50"
              >
                {submitting ? "Validation en cours..." : "Confirmer ma Commande"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Order Tracking Section */}
      <div className="rounded-3xl border border-slate-800 bg-[#0B0F19] p-6 sm:p-8 space-y-4">
        <h2 className="text-lg font-extrabold text-white">Suivre une Commande en Ligne</h2>
        <form onSubmit={handleTrackOrder} className="flex flex-wrap gap-3 max-w-xl">
          <input
            type="text"
            value={trackUid}
            onChange={(e) => setTrackUid(e.target.value)}
            placeholder="Entrez votre N° de commande (ex: WEB-20261114-XXXXX)"
            className="flex-1 rounded-xl border border-slate-800 bg-[#0F1420] px-4 py-2.5 text-xs text-white"
          />
          <button
            type="submit"
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white"
          >
            <Search className="h-4 w-4" /> Rechercher
          </button>
        </form>

        {trackError && <p className="text-xs text-rose-400">{trackError}</p>}

        {trackedOrder && (
          <div className="rounded-2xl border border-slate-800 bg-[#0F1420] p-5 text-xs space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <span className="font-mono font-bold text-blue-400">{trackedOrder.order_uid}</span>
                <span className="ml-3 text-slate-300">{trackedOrder.customer_name}</span>
              </div>
              <span className="rounded-full bg-blue-600/20 border border-blue-500/40 px-3 py-1 font-bold text-blue-300">
                Statut : {trackedOrder.status}
              </span>
            </div>
            <div className="space-y-1">
              {trackedOrder.items.map((it) => (
                <div key={it.id} className="flex justify-between text-slate-300">
                  <span>
                    {it.quantity} × {it.product_name} ({it.product_reference})
                  </span>
                  <span className="font-bold text-white">{formatMoney(it.line_total)}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between border-t border-slate-800 pt-2 font-extrabold text-white">
              <span>Total Commande</span>
              <span>{formatMoney(trackedOrder.total_amount)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

