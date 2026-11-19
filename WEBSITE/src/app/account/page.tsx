"use client";

import React, { useEffect, useState } from "react";
import {
  UserCheck,
  Clock,
  Shield,
  Package,
  LogIn,
  UserPlus,
  Building,
} from "lucide-react";
import { useStore } from "@/context/StoreContext";
import { apiFetch, formatMoney } from "@/lib/api";
import { CustomerProfile, OnlineOrder } from "@/types";

export default function AccountPage() {
  const { profile, setProfile, logout } = useStore();
  const [orders, setOrders] = useState<OnlineOrder[]>([]);
  const [tab, setTab] = useState<"login" | "register">("login");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Login state
  const [loginUser, setLoginUser] = useState("");
  const [loginPass, setLoginPass] = useState("");

  // Register state
  const [regUsername, setRegUsername] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regFirstName, setRegFirstName] = useState("");
  const [regLastName, setRegLastName] = useState("");
  const [regPhone, setRegPhone] = useState("");
  const [regRole, setRegRole] = useState<"PUBLIC" | "INSTALLER" | "RESELLER">("INSTALLER");
  const [regCompany, setRegCompany] = useState("");
  const [regWilaya, setRegWilaya] = useState("Alger");
  const [regRc, setRegRc] = useState("");
  const [regNif, setRegNif] = useState("");
  const [regJustification, setRegJustification] = useState("");

  useEffect(() => {
    if (profile) {
      apiFetch<{ profile: CustomerProfile; orders: OnlineOrder[] }>("/auth/me/")
        .then((res) => {
          setProfile(res.profile);
          setOrders(res.orders || []);
        })
        .catch(() => {});
    }
  }, [profile?.id]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const res = await apiFetch<{ access: string; refresh: string; profile: CustomerProfile }>(
        "/auth/login/",
        {
          method: "POST",
          body: JSON.stringify({ username: loginUser, password: loginPass }),
        }
      );
      localStorage.setItem("logisz_jwt_access", res.access);
      localStorage.setItem("logisz_jwt_refresh", res.refresh);
      localStorage.setItem("logisz_user_profile", JSON.stringify(res.profile));
      setProfile(res.profile);
    } catch (err: any) {
      setError(err.message || "Identifiants invalides.");
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const res = await apiFetch<{
        message: string;
        access: string;
        refresh: string;
        profile: CustomerProfile;
      }>("/auth/register/", {
        method: "POST",
        body: JSON.stringify({
          username: regUsername,
          email: regEmail,
          password: regPassword,
          first_name: regFirstName,
          last_name: regLastName,
          phone: regPhone,
          account_type: regRole,
          company_name: regCompany,
          wilaya: regWilaya,
          rc_number: regRc,
          nif_number: regNif,
          professional_justification: regJustification,
        }),
      });
      localStorage.setItem("logisz_jwt_access", res.access);
      localStorage.setItem("logisz_jwt_refresh", res.refresh);
      localStorage.setItem("logisz_user_profile", JSON.stringify(res.profile));
      setProfile(res.profile);
      setMessage(res.message);
    } catch (err: any) {
      setError(err.message || "Erreur lors de la création du compte.");
    }
  };

  if (profile) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10 space-y-8">
        {message && (
          <div className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-xs font-semibold text-emerald-300">
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          {/* Profile Summary Card */}
          <div className="lg:col-span-4 rounded-3xl border border-slate-800 bg-[#0F1420] p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600/20 text-blue-400">
                <Shield className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-lg font-extrabold text-white">{profile.username}</h1>
                <p className="text-xs text-slate-400">{profile.company_name || "Compte Client"}</p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-[#07090E] p-4 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Catégorie demandée :</span>
                <span className="font-bold text-white">{profile.requested_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Statut d&apos;approbation :</span>
                <span
                  className={`font-bold ${
                    profile.approval_status === "APPROVED"
                      ? "text-emerald-400"
                      : profile.approval_status === "PENDING"
                      ? "text-amber-400"
                      : "text-slate-300"
                  }`}
                >
                  {profile.approval_status}
                </span>
              </div>
              <div className="flex justify-between border-t border-slate-800 pt-2">
                <span className="text-slate-400">Tarif actif sur le site :</span>
                <span className="font-extrabold text-blue-400">{profile.effective_tier}</span>
              </div>
            </div>

            {profile.approval_status === "PENDING" && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-300 flex items-start gap-2">
                <Clock className="h-4 w-4 shrink-0 mt-0.5" />
                <span>
                  Votre demande d&apos;accès <b>{profile.requested_type}</b> est en cours d&apos;examen par l&apos;administrateur. Les prix affichés restent les tarifs publics jusqu&apos;à l&apos;approbation.
                </span>
              </div>
            )}

            {profile.approval_status === "APPROVED" && profile.effective_tier !== "PUBLIC" && (
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-300 flex items-start gap-2">
                <UserCheck className="h-4 w-4 shrink-0 mt-0.5" />
                <span>
                  Votre compte professionnel <b>{profile.effective_tier}</b> est actif ! Tous les prix du catalogue incluent automatiquement votre remise.
                </span>
              </div>
            )}

            <button
              onClick={logout}
              className="w-full rounded-xl border border-slate-700 bg-slate-800/70 py-2.5 text-xs font-bold text-slate-200 hover:bg-rose-600 hover:text-white transition-colors"
            >
              Se déconnecter
            </button>
          </div>

          {/* Order History */}
          <div className="lg:col-span-8 rounded-3xl border border-slate-800 bg-[#0F1420] p-6 space-y-4">
            <h2 className="flex items-center gap-2 text-lg font-extrabold text-white">
              <Package className="h-5 w-5 text-blue-400" />
              Historique de mes Commandes ({orders.length})
            </h2>

            {orders.length === 0 ? (
              <p className="text-xs text-slate-400 py-8 text-center">
                Vous n&apos;avez pas encore passé de commande sur ce compte.
              </p>
            ) : (
              <div className="space-y-3">
                {orders.map((o) => (
                  <div
                    key={o.id}
                    className="rounded-2xl border border-slate-800 bg-[#07090E] p-4 text-xs space-y-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-mono font-bold text-blue-400">{o.order_uid}</span>
                      <span className="rounded-full bg-blue-600/20 px-2.5 py-0.5 font-bold text-blue-300">
                        {o.status}
                      </span>
                    </div>
                    <div className="text-slate-400">
                      {o.items.map((it) => `${it.quantity}x ${it.product_name}`).join(" • ")}
                    </div>
                    <div className="flex justify-between pt-1 font-bold text-white">
                      <span>Tarif {o.applied_tier}</span>
                      <span className="text-emerald-400">{formatMoney(o.total_amount)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <div className="mb-8 flex justify-center gap-3">
        <button
          onClick={() => setTab("login")}
          className={`flex items-center gap-2 rounded-xl px-6 py-3 text-xs font-extrabold transition-all ${
            tab === "login"
              ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
              : "border border-slate-800 bg-[#0F1420] text-slate-300"
          }`}
        >
          <LogIn className="h-4 w-4" /> Connexion
        </button>
        <button
          onClick={() => setTab("register")}
          className={`flex items-center gap-2 rounded-xl px-6 py-3 text-xs font-extrabold transition-all ${
            tab === "register"
              ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
              : "border border-slate-800 bg-[#0F1420] text-slate-300"
          }`}
        >
          <UserPlus className="h-4 w-4" /> Ouverture de Compte (Installateur / Revendeur)
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-center text-xs font-bold text-rose-300">
          {error}
        </div>
      )}

      {tab === "login" ? (
        <form
          onSubmit={handleLogin}
          className="mx-auto max-w-md rounded-3xl border border-slate-800 bg-[#0F1420] p-8 space-y-5 shadow-2xl"
        >
          <div>
            <h1 className="text-xl font-extrabold text-white">Connexion Espace Client & Pro</h1>
            <p className="mt-1 text-xs text-slate-400">
              Connectez-vous pour accéder à vos tarifs Installateur ou Revendeur.
            </p>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-300">Nom d&apos;utilisateur ou Email</label>
              <input
                type="text"
                required
                value={loginUser}
                onChange={(e) => setLoginUser(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3.5 py-2.5 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">Mot de passe</label>
              <input
                type="password"
                required
                value={loginPass}
                onChange={(e) => setLoginPass(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3.5 py-2.5 text-xs text-white"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full rounded-xl bg-blue-600 py-3 text-xs font-extrabold text-white hover:bg-blue-500"
          >
            Se connecter
          </button>

          <div className="rounded-xl border border-slate-800 bg-[#07090E] p-3 text-[11px] text-slate-400 space-y-1">
            <div className="font-bold text-slate-300">Comptes de démonstration pré-configurés :</div>
            <div>• Admin : <code className="text-blue-400">admin</code> / <code className="text-blue-400">admin123</code></div>
            <div>• Installateur Approuvé : <code className="text-sky-400">installateur_pro</code> / <code className="text-sky-400">pro12345</code></div>
            <div>• Revendeur Approuvé : <code className="text-emerald-400">revendeur_gros</code> / <code className="text-emerald-400">gros12345</code></div>
          </div>
        </form>
      ) : (
        <form
          onSubmit={handleRegister}
          className="rounded-3xl border border-slate-800 bg-[#0F1420] p-8 space-y-5 shadow-2xl"
        >
          <div>
            <h1 className="text-xl font-extrabold text-white">
              Inscription & Demande d&apos;Accès Professionnel
            </h1>
            <p className="mt-1 text-xs text-slate-400">
              Choisissez votre profil. Les demandes Installateur et Revendeur sont vérifiées par l&apos;administrateur.
            </p>
          </div>

          {/* Account Category Selection */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {[
              { id: "PUBLIC", title: "Client Particulier", sub: "Accès immédiat aux tarifs publics" },
              { id: "INSTALLER", title: "Installateur CCTV", sub: "Tarifs préférentiels installateurs (après validation)" },
              { id: "RESELLER", title: "Revendeur / Grossiste", sub: "Grille tarifaire Gros B2B (après validation)" },
            ].map((role) => (
              <button
                type="button"
                key={role.id}
                onClick={() => setRegRole(role.id as any)}
                className={`rounded-2xl border p-4 text-left transition-all ${
                  regRole === role.id
                    ? "border-blue-500 bg-blue-600/15"
                    : "border-slate-800 bg-[#07090E]"
                }`}
              >
                <div className="text-xs font-extrabold text-white">{role.title}</div>
                <div className="mt-1 text-[11px] text-slate-400">{role.sub}</div>
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="text-xs font-semibold text-slate-300">Identifiant *</label>
              <input
                type="text"
                required
                value={regUsername}
                onChange={(e) => setRegUsername(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">Email *</label>
              <input
                type="email"
                required
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">Mot de passe *</label>
              <input
                type="password"
                required
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="text-xs font-semibold text-slate-300">Prénom</label>
              <input
                type="text"
                value={regFirstName}
                onChange={(e) => setRegFirstName(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">Nom</label>
              <input
                type="text"
                value={regLastName}
                onChange={(e) => setRegLastName(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">Téléphone *</label>
              <input
                type="text"
                required
                value={regPhone}
                onChange={(e) => setRegPhone(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-800 bg-[#07090E] px-3 py-2 text-xs text-white"
              />
            </div>
          </div>

          {regRole !== "PUBLIC" && (
            <div className="rounded-2xl border border-blue-500/30 bg-[#07090E] p-4 space-y-4">
              <div className="flex items-center gap-2 text-xs font-bold text-blue-400">
                <Building className="h-4 w-4" /> Informations Professionnelles ({regRole})
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <input
                  type="text"
                  placeholder="Nom de l'entreprise / Bureau"
                  value={regCompany}
                  onChange={(e) => setRegCompany(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-[#0F1420] px-3 py-2 text-xs text-white"
                />
                <input
                  type="text"
                  placeholder="N° Registre de Commerce (RC)"
                  value={regRc}
                  onChange={(e) => setRegRc(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-[#0F1420] px-3 py-2 text-xs text-white"
                />
                <input
                  type="text"
                  placeholder="NIF / Article Fiscal"
                  value={regNif}
                  onChange={(e) => setRegNif(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-[#0F1420] px-3 py-2 text-xs text-white"
                />
              </div>
              <textarea
                rows={2}
                placeholder="Décrivez votre activité (installations CCTV, revente informatique, chantiers...)"
                value={regJustification}
                onChange={(e) => setRegJustification(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-[#0F1420] p-3 text-xs text-white"
              />
            </div>
          )}

          <button
            type="submit"
            className="w-full rounded-xl bg-blue-600 py-3 text-xs font-extrabold text-white hover:bg-blue-500"
          >
            Créer mon compte et soumettre ma demande
          </button>
        </form>
      )}
    </div>
  );
}

