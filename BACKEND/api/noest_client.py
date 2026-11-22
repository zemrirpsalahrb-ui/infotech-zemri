# -*- coding: utf-8 -*-
"""
Client API pour la société de livraison NOEST (Algérie)
Base URL: https://app.noest-dz.com
Documentation: NOEST Public API v2.4
"""

import json
import logging
import urllib.request
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)

NOEST_BASE_URL = getattr(settings, "NOEST_API_BASE_URL", "https://app.noest-dz.com").rstrip("/")
NOEST_TOKEN = getattr(settings, "NOEST_API_TOKEN", "60TAGGo3ZQWdifzKVmmPWSBlVVz7bhOXnwn")
NOEST_USER_GUID = getattr(settings, "NOEST_USER_GUID", "02VXZWSF")

# Cache mémoire pour éviter de surcharger l'API NOEST
_CACHE_FEES = None
_CACHE_WILAYAS = None
_CACHE_DESKS = None
_CACHE_COMMUNES = {}

def _make_request(endpoint, method="GET", data=None):
    url = f"{NOEST_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {NOEST_TOKEN}",
        "Accept": "application/json",
        "User-Agent": "INFOTECH-ZEMRI-LOGISZ/1.0",
    }
    encoded_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        encoded_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            raw = res.read().decode("utf-8")
            if res.headers.get_content_type() == "application/pdf":
                return {"success": True, "pdf_bytes": raw}
            try:
                return json.loads(raw)
            except Exception:
                return {"success": True, "raw": raw}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
            return {"success": False, "error": parsed, "status": e.code}
        except Exception:
            return {"success": False, "error": err_body, "status": e.code}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_wilayas():
    global _CACHE_WILAYAS
    if _CACHE_WILAYAS:
        return _CACHE_WILAYAS
    res = _make_request("/api/public/get/wilayas")
    if isinstance(res, list):
        _CACHE_WILAYAS = res
        return res
    return []

def get_fees():
    global _CACHE_FEES
    if _CACHE_FEES:
        return _CACHE_FEES
    res = _make_request("/api/public/fees")
    if isinstance(res, dict) and "tarifs" in res:
        _CACHE_FEES = res
        return res
    return {}

def get_desks():
    global _CACHE_DESKS
    if _CACHE_DESKS:
        return _CACHE_DESKS
    res = _make_request("/api/public/desks")
    if isinstance(res, dict):
        _CACHE_DESKS = res
        return res
    return {}

def get_communes(wilaya_id=None):
    global _CACHE_COMMUNES
    key = str(wilaya_id) if wilaya_id else "all"
    if key in _CACHE_COMMUNES:
        return _CACHE_COMMUNES[key]
    
    endpoint = f"/api/public/get/communes/{wilaya_id}" if wilaya_id else "/api/public/get/communes"
    res = _make_request(endpoint)
    if isinstance(res, (dict, list)):
        # Normalize into list of communes
        communes_list = list(res.values()) if isinstance(res, dict) else res
        _CACHE_COMMUNES[key] = communes_list
        return communes_list
    return []

def sanitize_algerian_phone(phone_str):
    """
    Nettoie et formate le numéro de téléphone pour NOEST (9 ou 10 chiffres).
    Ex: +213 557 88 27 19 -> 0557882719
    """
    digits = "".join(filter(str.isdigit, str(phone_str or "")))
    if digits.startswith("213") and len(digits) >= 12:
        digits = "0" + digits[3:]
    elif not digits.startswith("0") and len(digits) == 9:
        digits = "0" + digits
    return digits[:10]

def create_noest_order(order, wilaya_id=None, commune_name="", stop_desk=0, station_code=""):
    """
    Envoie une commande vers l'API de livraison NOEST.
    POST /api/public/create/order
    """
    # 1. Wilaya ID
    w_id = wilaya_id
    if not w_id:
        # Essayer de mapper le nom de la wilaya vers son ID
        wilayas = get_wilayas()
        order_w_str = str(order.wilaya or "").strip().lower()
        for w in wilayas:
            if str(w.get("code")) == order_w_str or str(w.get("nom", "")).lower() in order_w_str or order_w_str in str(w.get("nom", "")).lower():
                w_id = w.get("code")
                break
        if not w_id:
            w_id = 31 # Default Oran if completely unknown

    # 2. Commune
    commune = (commune_name or getattr(order, "delivery_commune", "") or "").strip()
    if not commune:
        # Récupérer la première commune de la wilaya comme fallback
        comms = get_communes(w_id)
        if comms:
            commune = comms[0].get("nom", "Centre")
        else:
            commune = str(order.wilaya or "Oran")

    # 3. Résumé des produits
    items = order.items.all()
    if items.exists():
        product_summary = ", ".join([f"{int(it.quantity)}x {it.product_name or it.product_reference}" for it in items])
    else:
        product_summary = "Équipements de vidéosurveillance Dahua"
    # Tronquer si trop long
    product_summary = product_summary[:250]

    # 4. Nettoyage du téléphone
    phone = sanitize_algerian_phone(order.customer_phone)

    # 5. Adresse
    address = (order.delivery_address or f"Wilaya {order.wilaya}, {commune}").strip()[:255]

    # 6. Stop desk
    is_stop_desk = 1 if (stop_desk or getattr(order, "delivery_stop_desk", False)) else 0
    st_code = (station_code or getattr(order, "delivery_station_code", "") or "").strip()

    if is_stop_desk and not st_code:
        # Trouver la première station de la wilaya en fallback
        try:
            desks = get_desks()
            w_prefix = f"{int(w_id):02d}"
            for k, d in desks.items():
                if k.startswith(w_prefix) or str(d.get("code", "")).startswith(str(w_id)):
                    st_code = d.get("code") or k
                    break
        except Exception:
            pass

    payload = {
        "user_guid": NOEST_USER_GUID,
        "reference": str(order.order_uid)[:40],
        "client": str(order.customer_name)[:255],
        "phone": phone,
        "adresse": address,
        "wilaya_id": int(w_id),
        "montant": float(order.total_amount),
        "produit": product_summary,
        "type_id": 1, # 1 = Livraison standard avec encaissement (Cash à la livraison)
        "stop_desk": is_stop_desk,
        "remarque": f"Commande en ligne {order.order_uid}" + (f" - {order.notes}" if order.notes else "")
    }

    if is_stop_desk:
        if st_code:
            payload["station_code"] = st_code
    else:
        payload["commune"] = commune

    logger.info(f"Envoi de la commande {order.order_uid} à NOEST : {payload}")
    res = _make_request("/api/public/create/order", method="POST", data=payload)
    return res

def validate_noest_order(tracking_code):
    """
    Valide une commande NOEST afin qu'elle apparaisse pour la logistique.
    POST /api/public/valid/order
    """
    payload = {
        "user_guid": NOEST_USER_GUID,
        "tracking": tracking_code
    }
    return _make_request("/api/public/valid/order", method="POST", data=payload)

def track_noest_order(tracking_code):
    """
    Récupère le suivi et l'historique d'une commande NOEST.
    POST /api/public/get/trackings/info
    """
    payload = {
        "trackings": [tracking_code]
    }
    return _make_request("/api/public/get/trackings/info", method="POST", data=payload)
