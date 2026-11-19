"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { CartItem, CustomerProfile, Product } from "@/types";
import { apiFetch } from "@/lib/api";

interface StoreContextValue {
  profile: CustomerProfile | null;
  setProfile: (p: CustomerProfile | null) => void;
  logout: () => void;
  refreshProfile: () => Promise<void>;
  cart: CartItem[];
  addToCart: (product: Product, quantity?: number) => void;
  updateCartQty: (productId: number, quantity: number) => void;
  removeFromCart: (productId: number) => void;
  clearCart: () => void;
  cartCount: number;
  cartTotal: number;
  compareList: Product[];
  toggleCompare: (product: Product) => void;
  clearCompare: () => void;
}

const StoreContext = createContext<StoreContextValue | undefined>(undefined);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [compareList, setCompareList] = useState<Product[]>([]);

  useEffect(() => {
    try {
      const savedCart = localStorage.getItem("logisz_cctv_cart");
      if (savedCart) setCart(JSON.parse(savedCart));
      const savedProfile = localStorage.getItem("logisz_user_profile");
      if (savedProfile) setProfile(JSON.parse(savedProfile));
    } catch {
      // ignore localStorage read errors
    }
    refreshProfile();
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("logisz_cctv_cart", JSON.stringify(cart));
    } catch {
      // ignore
    }
  }, [cart]);

  const refreshProfile = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("logisz_jwt_access") : null;
    if (!token) return;
    try {
      const data = await apiFetch<{ profile: CustomerProfile }>("/auth/me/");
      if (data?.profile) {
        setProfile(data.profile);
        localStorage.setItem("logisz_user_profile", JSON.stringify(data.profile));
      }
    } catch {
      // token expired or invalid
    }
  };

  const logout = () => {
    localStorage.removeItem("logisz_jwt_access");
    localStorage.removeItem("logisz_jwt_refresh");
    localStorage.removeItem("logisz_user_profile");
    setProfile(null);
  };

  const addToCart = (product: Product, quantity = 1) => {
    setCart((prev) => {
      const idx = prev.findIndex((item) => item.product.id === product.id);
      if (idx >= 0) {
        const updated = [...prev];
        updated[idx] = { ...updated[idx], product, quantity: updated[idx].quantity + quantity };
        return updated;
      }
      return [...prev, { product, quantity }];
    });
  };

  const updateCartQty = (productId: number, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart((prev) =>
      prev.map((item) => (item.product.id === productId ? { ...item, quantity } : item))
    );
  };

  const removeFromCart = (productId: number) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId));
  };

  const clearCart = () => setCart([]);

  const toggleCompare = (product: Product) => {
    setCompareList((prev) => {
      if (prev.some((p) => p.id === product.id)) {
        return prev.filter((p) => p.id !== product.id);
      }
      if (prev.length >= 4) {
        return [...prev.slice(1), product];
      }
      return [...prev, product];
    });
  };

  const clearCompare = () => setCompareList([]);

  const cartCount = cart.reduce((acc, item) => acc + item.quantity, 0);
  const cartTotal = cart.reduce(
    (acc, item) => acc + Number(item.product.effective_price) * item.quantity,
    0
  );

  return (
    <StoreContext.Provider
      value={{
        profile,
        setProfile,
        logout,
        refreshProfile,
        cart,
        addToCart,
        updateCartQty,
        removeFromCart,
        clearCart,
        cartCount,
        cartTotal,
        compareList,
        toggleCompare,
        clearCompare,
      }}
    >
      {children}
    </StoreContext.Provider>
  );
}

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used within StoreProvider");
  return ctx;
}

