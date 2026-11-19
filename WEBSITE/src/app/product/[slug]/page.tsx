"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ShoppingCart,
  ShieldCheck,
  CheckCircle2,
  Star,
  ZoomIn,
  Layers,
  Lock,
  MessageCircle,
  Send,
} from "lucide-react";
import { apiFetch, buildWhatsAppLink, formatMoney } from "@/lib/api";
import { Product } from "@/types";
import { useStore } from "@/context/StoreContext";
import ProductCard from "@/components/ProductCard";

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=1000&q=80";

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const { addToCart, toggleCompare, profile } = useStore();

  const [product, setProduct] = useState<Product | null>(null);
  const [related, setRelated] = useState<Product[]>([]);
  const [selectedImage, setSelectedImage] = useState<string>("");
  const [zoomed, setZoomed] = useState(false);
  const [qty, setQty] = useState(1);
  const [loading, setLoading] = useState(true);

  // Review form state
  const [rating, setRating] = useState(5);
  const [reviewTitle, setReviewTitle] = useState("");
  const [reviewComment, setReviewComment] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [reviewMsg, setReviewMsg] = useState("");

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    apiFetch<{ product: Product; related_products: Product[] }>(`/products/${encodeURIComponent(slug)}/`)
      .then((res) => {
        setProduct(res.product);
        setRelated(res.related_products || []);
        setSelectedImage(res.product.main_image || FALLBACK_IMAGE);
      })
      .catch(() => setProduct(null))
      .finally(() => setLoading(false));
  }, [slug]);

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product) return;
    setReviewMsg("");
    try {
      const res = await apiFetch<{ message: string }>(`/products/${product.id}/reviews/`, {
        method: "POST",
        body: JSON.stringify({
          rating,
          title: reviewTitle,
          comment: reviewComment,
          author_name: authorName || profile?.username || "Client",
        }),
      });
      setReviewMsg(res.message);
      setReviewTitle("");
      setReviewComment("");
    } catch (err: any) {
      setReviewMsg(err.message || "Erreur lors de l'envoi de l'avis.");
    }
  };

  if (loading) {
    return <div className="mx-auto max-w-7xl px-4 py-16 text-center text-slate-400">Chargement de la fiche technique...</div>;
  }

  if (!product) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center space-y-4">
        <h1 className="text-2xl font-bold text-white">Produit introuvable</h1>
        <Link href="/catalog" className="inline-block rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white">
          Retour au catalogue
        </Link>
      </div>
    );
  }

  const gallery = product.images?.length
    ? product.images.map((i) => i.image_url)
    : [product.main_image || FALLBACK_IMAGE];

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 space-y-16">
      {/* Main Product Section */}
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
        {/* Left: Image Gallery & Zoom */}
        <div className="lg:col-span-6 space-y-4">
          <div
            onClick={() => setZoomed(!zoomed)}
            className="group relative aspect-[4/3] cursor-zoom-in overflow-hidden rounded-3xl border border-slate-800 bg-[#0F1420]"
          >
            <img
              src={selectedImage || FALLBACK_IMAGE}
              alt={product.name}
              className={`h-full w-full object-cover transition-transform duration-500 ${
                zoomed ? "scale-150" : "group-hover:scale-105"
              }`}
            />
            <div className="absolute bottom-3 right-3 flex items-center gap-1 rounded-lg bg-black/70 px-2.5 py-1 text-[11px] text-slate-300 backdrop-blur-md">
              <ZoomIn className="h-3.5 w-3.5" />
              <span>Cliquer pour zoomer</span>
            </div>
          </div>

          {gallery.length > 1 && (
            <div className="flex gap-3 overflow-x-auto pb-2">
              {gallery.map((url, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(url)}
                  className={`h-20 w-24 shrink-0 overflow-hidden rounded-xl border-2 transition-all ${
                    selectedImage === url ? "border-blue-500" : "border-slate-800 opacity-70 hover:opacity-100"
                  }`}
                >
                  <img src={url} alt="" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Product Info & Dynamic Pricing */}
        <div className="lg:col-span-6 space-y-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-lg bg-blue-600/15 px-2.5 py-1 font-mono font-semibold text-blue-400">
                Réf: {product.reference}
              </span>
              <span className="rounded-lg bg-slate-800 px-2.5 py-1 font-semibold text-slate-300">
                {product.brand_name}
              </span>
              <span className="rounded-lg bg-slate-800/60 px-2.5 py-1 text-slate-400">
                {product.category_name}
              </span>
            </div>

            <h1 className="text-2xl font-extrabold text-white sm:text-3xl">
              {product.name}
            </h1>

            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1 text-amber-400">
                <Star className="h-4 w-4 fill-amber-400" />
                <span className="font-bold text-white">{product.avg_rating}</span>
                <span className="text-slate-400">({product.review_count} avis vérifiés)</span>
              </div>
              <span className="text-slate-600">|</span>
              {product.in_stock ? (
                <span className="flex items-center gap-1 font-semibold text-emerald-400">
                  <CheckCircle2 className="h-4 w-4" />
                  Stock disponible ({product.available_stock} unités)
                </span>
              ) : (
                <span className="font-semibold text-amber-400">Sur commande</span>
              )}
            </div>
          </div>

          {/* Dynamic Tier Pricing Box */}
          <div className="rounded-2xl border border-blue-500/30 bg-[#0F1420] p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
                Tarif Appliqué ({product.applied_tier})
              </span>
              <span className="flex items-center gap-1 text-xs text-slate-400">
                <ShieldCheck className="h-4 w-4 text-blue-400" />
                Garantie officielle {product.warranty_months} mois
              </span>
            </div>

            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-extrabold text-white">
                {formatMoney(product.effective_price)}
              </span>
              {product.effective_price < product.public_price && (
                <span className="text-sm text-slate-500 line-through">
                  Prix public : {formatMoney(product.public_price)}
                </span>
              )}
            </div>

            {/* Tier Breakdown for Approved Pro Accounts vs Public Notice */}
            {product.applied_tier === "PUBLIC" ? (
              <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-[#07090E] p-3 text-xs">
                <div className="flex items-center gap-2 text-slate-300">
                  <Lock className="h-4 w-4 text-sky-400 shrink-0" />
                  <span>Vous êtes Installateur ou Revendeur ? Débloquez vos tarifs B2B.</span>
                </div>
                <Link href="/account" className="font-bold text-blue-400 hover:underline shrink-0 ml-2">
                  Accès Pro →
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
                <div className="rounded-lg bg-[#07090E] p-2.5 border border-slate-800">
                  <span className="text-slate-400 block">Prix Public</span>
                  <span className="font-bold text-slate-200">{formatMoney(product.tier_prices.public_price)}</span>
                </div>
                {product.tier_prices.installer_price && (
                  <div className="rounded-lg bg-[#07090E] p-2.5 border border-sky-500/30">
                    <span className="text-sky-400 block">Prix Installateur</span>
                    <span className="font-bold text-white">{formatMoney(product.tier_prices.installer_price)}</span>
                  </div>
                )}
                {product.tier_prices.reseller_price && (
                  <div className="rounded-lg bg-[#07090E] p-2.5 border border-emerald-500/30">
                    <span className="text-emerald-400 block">Prix Revendeur Gros</span>
                    <span className="font-bold text-white">{formatMoney(product.tier_prices.reseller_price)}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          <p className="text-sm text-slate-300 leading-relaxed">
            {product.description || product.short_description}
          </p>

          {/* Add to Cart & Actions */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <div className="flex items-center rounded-xl border border-slate-800 bg-[#0F1420]">
              <button
                onClick={() => setQty(Math.max(1, qty - 1))}
                className="px-3.5 py-2.5 text-sm font-bold text-slate-300 hover:text-white"
              >
                -
              </button>
              <input
                type="number"
                min={1}
                value={qty}
                onChange={(e) => setQty(Math.max(1, Number(e.target.value) || 1))}
                className="w-14 bg-transparent text-center text-sm font-bold text-white focus:outline-none"
              />
              <button
                onClick={() => setQty(qty + 1)}
                className="px-3.5 py-2.5 text-sm font-bold text-slate-300 hover:text-white"
              >
                +
              </button>
            </div>

            <button
              onClick={() => addToCart(product, qty)}
              className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-bold text-white shadow-xl shadow-blue-600/25 hover:bg-blue-500 transition-all"
            >
              <ShoppingCart className="h-4 w-4" />
              <span>Ajouter au panier</span>
            </button>

            <button
              onClick={() => toggleCompare(product)}
              className="rounded-xl border border-slate-800 bg-[#0F1420] p-3 text-slate-300 hover:border-blue-500/50 hover:text-blue-400"
              title="Comparer"
            >
              <Layers className="h-5 w-5" />
            </button>
          </div>

          {/* WhatsApp Direct Product Inquiry */}
          <a
            href={buildWhatsAppLink(
              process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "+213550000000",
              `Bonjour LOGISZ, je souhaite commander / avoir des informations sur : ${product.name} (Réf: ${product.reference}).`
            )}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-400 hover:underline"
          >
            <MessageCircle className="h-4 w-4" />
            Demander une fiche ou disponibilité immédiate sur WhatsApp
          </a>
        </div>
      </div>

      {/* Technical Specifications & Reviews */}
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
        {/* Technical Specifications */}
        <div className="lg:col-span-6 space-y-4">
          <h2 className="text-xl font-extrabold text-white">Fiche Technique & Spécifications</h2>
          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-[#0F1420]">
            <table className="w-full text-left text-xs">
              <tbody className="divide-y divide-slate-800/80">
                <tr>
                  <td className="p-3.5 font-semibold text-slate-400 w-1/3">Référence Officielle</td>
                  <td className="p-3.5 font-mono text-white">{product.reference}</td>
                </tr>
                <tr>
                  <td className="p-3.5 font-semibold text-slate-400">Marque</td>
                  <td className="p-3.5 text-white">{product.brand_name}</td>
                </tr>
                <tr>
                  <td className="p-3.5 font-semibold text-slate-400">Garantie</td>
                  <td className="p-3.5 text-white">{product.warranty_months} mois</td>
                </tr>
                {Object.entries(product.technical_specs || {}).map(([key, val]) => (
                  <tr key={key}>
                    <td className="p-3.5 font-semibold text-slate-400">{key}</td>
                    <td className="p-3.5 text-slate-200">{val}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Customer Reviews & Rating Moderation */}
        <div className="lg:col-span-6 space-y-6">
          <h2 className="text-xl font-extrabold text-white">
            Avis Clients & Installateurs ({product.approved_reviews?.length || 0})
          </h2>

          <div className="space-y-3">
            {(product.approved_reviews || []).length === 0 ? (
              <p className="text-xs text-slate-400">Aucun avis publié pour le moment. Soyez le premier à donner votre avis !</p>
            ) : (
              product.approved_reviews?.map((rev) => (
                <div key={rev.id} className="rounded-2xl border border-slate-800 bg-[#0F1420] p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{rev.author_name}</span>
                      {rev.is_verified_purchase && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                          <CheckCircle2 className="h-3 w-3" /> Achat Vérifié
                        </span>
                      )}
                    </div>
                    <div className="flex text-amber-400">
                      {Array.from({ length: rev.rating }).map((_, i) => (
                        <Star key={i} className="h-3.5 w-3.5 fill-amber-400" />
                      ))}
                    </div>
                  </div>
                  {rev.title && <div className="text-xs font-bold text-slate-200">{rev.title}</div>}
                  <p className="text-xs text-slate-300">{rev.comment}</p>
                  {rev.admin_reply && (
                    <div className="mt-2 rounded-xl border border-blue-500/30 bg-[#07090E] p-2.5 text-xs text-blue-300">
                      <span className="font-bold">Réponse LOGISZ : </span>
                      {rev.admin_reply}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Submit Review Form */}
          <form
            onSubmit={handleReviewSubmit}
            className="rounded-2xl border border-slate-800 bg-[#0F1420] p-5 space-y-3"
          >
            <h3 className="text-sm font-bold text-white">Laisser un avis sur ce produit</h3>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Votre nom ou entreprise"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
                className="rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
              />
              <select
                value={rating}
                onChange={(e) => setRating(Number(e.target.value))}
                className="rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
              >
                <option value={5}>★★★★★ (5/5 Excellent)</option>
                <option value={4}>★★★★☆ (4/5 Très bien)</option>
                <option value={3}>★★★☆☆ (3/5 Correct)</option>
                <option value={2}>★★☆☆☆ (2/5 Moyen)</option>
                <option value={1}>★☆☆☆☆ (1/5 Insuffisant)</option>
              </select>
            </div>
            <input
              type="text"
              placeholder="Titre de votre avis"
              value={reviewTitle}
              onChange={(e) => setReviewTitle(e.target.value)}
              className="w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
            />
            <textarea
              rows={3}
              required
              placeholder="Partagez votre retour d'installation ou d'utilisation..."
              value={reviewComment}
              onChange={(e) => setReviewComment(e.target.value)}
              className="w-full rounded-xl border border-slate-800 bg-[#07090E] p-3 text-xs text-white"
            />
            {reviewMsg && <p className="text-xs text-emerald-400">{reviewMsg}</p>}
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-500"
            >
              <Send className="h-3.5 w-3.5" /> Envoyer mon avis
            </button>
          </form>
        </div>
      </div>

      {/* Related Products */}
      {related.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-extrabold text-white">Produits Compatibles & Similaires</h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {related.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

