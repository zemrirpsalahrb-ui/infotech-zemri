export type CustomerTier = "PUBLIC" | "INSTALLER" | "RESELLER" | "ADMIN";
export type ApprovalStatus = "NONE" | "PENDING" | "APPROVED" | "REJECTED" | "SUSPENDED";

export interface CustomerProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  account_type: CustomerTier;
  requested_type: CustomerTier;
  approval_status: ApprovalStatus;
  effective_tier: CustomerTier;
  is_admin: boolean;
  phone: string;
  company_name: string;
  wilaya: string;
  address: string;
  rc_number: string;
  nif_number: string;
  professional_justification: string;
  admin_notes?: string;
  created_at: string;
}

export interface ProductImage {
  id: number;
  product: number;
  image_url: string;
  alt_text: string;
  is_main: boolean;
  sort_order: number;
}

export interface Review {
  id: number;
  product: number;
  product_name?: string;
  product_reference?: string;
  author_name: string;
  rating: number;
  title: string;
  comment: string;
  is_verified_purchase: boolean;
  status: "PENDING" | "APPROVED" | "HIDDEN";
  admin_reply: string;
  created_at: string;
}

export interface Product {
  id: number;
  desktop_ide: number | null;
  reference: string;
  name: string;
  slug: string;
  category: number | null;
  category_name: string;
  category_slug: string;
  brand: number | null;
  brand_name: string;
  brand_raw: string;
  public_price: number;
  promo_price: number | null;
  effective_price: number;
  applied_tier: CustomerTier;
  tier_prices: {
    public_price: number;
    promo_price?: number | null;
    installer_price?: number;
    reseller_price?: number;
    special_price?: number | null;
  };
  tva_rate: number;
  physical_stock: number;
  reserved_stock: number;
  available_stock: number;
  in_stock: boolean;
  short_description: string;
  description: string;
  technical_specs: Record<string, string>;
  warranty_months: number;
  kit_component_type:
    | "NONE"
    | "CAMERA"
    | "RECORDER"
    | "HDD"
    | "PSU"
    | "CABLE"
    | "CONNECTOR"
    | "ACCESSORY"
    | "COMPLETE_KIT";
  kit_technology: "ALL" | "ANALOG_HD" | "IP" | "WIFI";
  kit_channels: number;
  compatibility_notes: string;
  is_featured: boolean;
  is_bestseller: boolean;
  is_new_arrival: boolean;
  is_special_offer: boolean;
  is_active: boolean;
  main_image: string;
  images: ProductImage[];
  avg_rating: number;
  review_count: number;
  approved_reviews?: Review[];
  last_desktop_sync?: string | null;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon_name: string;
  image_url: string;
  sort_order: number;
  product_count: number;
}

export interface Brand {
  id: number;
  name: string;
  slug: string;
  logo_url: string;
  description: string;
  is_featured: boolean;
  product_count: number;
}

export interface Banner {
  id: number;
  title: string;
  subtitle: string;
  badge_text: string;
  cta_text: string;
  cta_link: string;
  image_url: string;
  accent_color: string;
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export interface OnlineOrderItem {
  id: number;
  product: number | null;
  desktop_ide: number | null;
  product_reference: string;
  product_name: string;
  quantity: number;
  applied_unit_price: number;
  public_unit_price_snapshot: number;
  line_total: number;
}

export type OrderStatus =
  | "NEW"
  | "PENDING"
  | "CONFIRMED"
  | "PREPARING"
  | "READY_FOR_PICKUP"
  | "SHIPPED"
  | "DELIVERED"
  | "CANCELLED"
  | "REJECTED";

export interface OnlineOrder {
  id: number;
  order_uid: string;
  customer_name: string;
  customer_phone: string;
  customer_email: string;
  company_name: string;
  wilaya: string;
  delivery_address: string;
  notes: string;
  applied_tier: CustomerTier;
  delivery_method: "DELIVERY" | "PICKUP";
  payment_method: "CASH_ON_DELIVERY" | "PAY_AT_STORE" | "BANK_TRANSFER" | "CIB_EDAHABIA";
  status: OrderStatus;
  subtotal: number;
  shipping_fee: number;
  total_amount: number;
  reservation_active: boolean;
  has_stock_conflict: boolean;
  conflict_details: string;
  pos_converted: boolean;
  pos_bon_number: string;
  pos_converted_at?: string | null;
  pos_converted_by?: string;
  items: OnlineOrderItem[];
  created_at: string;
}

