import io
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128


def fmt_currency(val):
    try:
        d = Decimal(str(val or 0))
        return f"{d:,.2f} DA".replace(",", " ").replace(".", ",")
    except Exception:
        return f"{val} DA"


def generate_bon_pdf(bon_data, store_info=None):
    """
    Génère un Bon de Vente au format PDF (A4 compact / demi-feuille)
    strictement conforme au modèle de facturation du logiciel LOGISZ (InvoicePdf.java).
    Retourne un buffer binaire (io.BytesIO).
    """
    if store_info is None:
        store_info = {
            "nom": "ZEMRI ABDESSAMAD",
            "enseigne": "INFOTECH ZEMRI - SYSTÈMES DE SÉCURITÉ & CCTV",
            "adresse": "4 BVD DIDDOUCHE MOURAD, ORAN",
            "tel": "0791 47 63 04",
            "rc": "15 A 0608466",
            "nif": "196631011235439",
            "n_article": "3153082074",
            "banque": "BADR N° 963000114030058",
        }

    buffer = io.BytesIO()

    # Marges compactes identiques au logiciel Java (28pt ~ 10mm, 14pt ~ 5mm)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
    )

    styles = getSampleStyleSheet()

    title_store = ParagraphStyle(
        "StoreTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
    )
    store_meta = ParagraphStyle(
        "StoreMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#475569"),
    )
    doc_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        alignment=2,  # Right
        textColor=colors.HexColor("#2563eb"),
    )
    doc_ref = ParagraphStyle(
        "DocRef",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        alignment=2,  # Right
        textColor=colors.HexColor("#0f172a"),
    )
    doc_date = ParagraphStyle(
        "DocDate",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=2,  # Right
        textColor=colors.HexColor("#334155"),
    )
    client_title = ParagraphStyle(
        "ClientTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )
    client_detail = ParagraphStyle(
        "ClientDetail",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#475569"),
    )
    tbl_header = ParagraphStyle(
        "TblHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=9,
        alignment=1,  # Center
        textColor=colors.white,
    )
    tbl_cell = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    tbl_cell_center = ParagraphStyle(
        "TblCellCenter",
        parent=tbl_cell,
        alignment=1,
    )
    tbl_cell_right = ParagraphStyle(
        "TblCellRight",
        parent=tbl_cell,
        alignment=2,
    )
    totaux_label = ParagraphStyle(
        "TotauxLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    totaux_val = ParagraphStyle(
        "TotauxVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        alignment=2,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # ==========================================
    # 1. EN-TÊTE : Magasin (Gauche) | Bon + Client (Droite)
    # ==========================================
    mag_paras = [
        Paragraph(store_info.get("nom", "INFOTECH ZEMRI"), title_store),
        Spacer(1, 1 * mm),
        Paragraph(store_info.get("enseigne", ""), store_meta),
        Paragraph(f"Adresse : {store_info.get('adresse', '')}", store_meta),
        Paragraph(f"Tél : {store_info.get('tel', '')}", store_meta),
    ]
    if store_info.get("rc"):
        mag_paras.append(
            Paragraph(
                f"RC : {store_info.get('rc')} | NIF : {store_info.get('nif')}",
                store_meta,
            )
        )

    nom_client = bon_data.get("nom_de_client") or bon_data.get("client") or "Passager"
    tel_client = bon_data.get("tel_client") or bon_data.get("tel") or ""
    n_bon = bon_data.get("bon") or bon_data.get("n_facture") or "-"
    date_bon = bon_data.get("date") or bon_data.get("date_vente") or "-"

    client_box = [
        Paragraph(f"CLIENT : {nom_client}", client_title),
    ]
    if tel_client and tel_client != "/":
        client_box.append(Paragraph(f"Tél : {tel_client}", client_detail))
    if bon_data.get("adresse_client"):
        client_box.append(
            Paragraph(f"Adresse : {bon_data.get('adresse_client')}", client_detail)
        )

    t_client_box = Table(
        [[client_box]],
        colWidths=[80 * mm],
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ],
    )

    right_paras = [
        Paragraph("BON DE VENTE", doc_title),
        Paragraph(f"N° {n_bon}", doc_ref),
        Paragraph(f"Date : {date_bon}", doc_date),
        Spacer(1, 2 * mm),
        t_client_box,
    ]

    header_table = Table(
        [[mag_paras, right_paras]],
        colWidths=[105 * mm, 85 * mm],
        style=[
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ],
    )
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # ==========================================
    # 2. TABLEAU DES ARTICLES DU BON
    # ==========================================
    tbl_data = [
        [
            Paragraph("Référence", tbl_header),
            Paragraph("Désignation", tbl_header),
            Paragraph("Qté", tbl_header),
            Paragraph("Prix unit.", tbl_header),
            Paragraph("Total", tbl_header),
        ]
    ]

    lignes = bon_data.get("lignes") or bon_data.get("items") or []

    # Si pas de liste structurée, parser le champ string `articles`
    if not lignes and bon_data.get("articles"):
        raw_art = str(bon_data.get("articles") or "").strip()
        parts = [p.strip() for p in raw_art.split(",") if p.strip()]
        for p in parts:
            qte = "1"
            nom_p = p
            if "x " in p:
                spl = p.split("x ", 1)
                qte = spl[0].replace(".00", "")
                nom_p = spl[1]
            lignes.append({
                "ref": "-",
                "designation": nom_p,
                "qte": qte,
                "prix": "-",
                "total": "-",
            })

    if not lignes:
        lignes.append({
            "ref": "-",
            "designation": "Règlement / Vente diverse",
            "qte": "1",
            "prix": fmt_currency(bon_data.get("total", 0)),
            "total": fmt_currency(bon_data.get("total", 0)),
        })

    row_idx = 0
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8 * mm),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
    ]

    for item in lignes:
        row_idx += 1
        ref = item.get("ref") or item.get("reference") or "-"
        desig = item.get("designation") or item.get("produit") or item.get("name") or "-"
        qte = str(item.get("qte") or item.get("quantite") or "1").replace(".00", "")
        prix = item.get("prix") or item.get("prix_unitaire") or item.get("unit_price")
        tot = item.get("total") or item.get("montant") or item.get("line_total")

        prix_str = fmt_currency(prix) if prix not in (None, "-") else "-"
        tot_str = fmt_currency(tot) if tot not in (None, "-") else "-"

        bg_color = colors.HexColor("#f8fafc") if row_idx % 2 == 1 else colors.white
        t_style.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg_color))

        tbl_data.append([
            Paragraph(str(ref), tbl_cell_center),
            Paragraph(str(desig), tbl_cell),
            Paragraph(str(qte), tbl_cell_center),
            Paragraph(prix_str, tbl_cell_right),
            Paragraph(tot_str, tbl_cell_right),
        ])

    table_articles = Table(
        tbl_data,
        colWidths=[28 * mm, 82 * mm, 18 * mm, 31 * mm, 31 * mm],
        style=t_style,
    )
    story.append(table_articles)
    story.append(Spacer(1, 3 * mm))

    # ==========================================
    # 3. TOTAUX & SOLDE (En bas à droite)
    # ==========================================
    total_bon = Decimal(str(bon_data.get("total") or bon_data.get("total_amount") or 0))
    verse = Decimal(str(bon_data.get("verse") if bon_data.get("verse") is not None else (bon_data.get("versement") or 0)))
    ancien = Decimal(str(bon_data.get("ancien") if bon_data.get("ancien") is not None else (bon_data.get("ancien_solde") or 0)))
    nouveau = Decimal(str(bon_data.get("solde") if bon_data.get("solde") is not None else (bon_data.get("nouveau_solde") or 0)))
    credit_bon = max(Decimal("0.00"), total_bon - verse)
    nom_c = (bon_data.get("nom_de_client") or "").strip().lower()
    is_passager = nom_c in ("passager", "client comptoir", "")

    totaux_rows = [
        [Paragraph("Total du bon :", totaux_label), Paragraph(fmt_currency(total_bon), totaux_val)],
        [Paragraph("Montant versé :", totaux_label), Paragraph(fmt_currency(verse), totaux_val)],
    ]

    # Crédit accordé sur ce bon (si non réglé en totalité)
    if credit_bon > Decimal("0.009"):
        p_credit_bon = ParagraphStyle(
            "CreditBonVal",
            parent=totaux_val,
            textColor=colors.HexColor("#dc2626"),  # Rouge
            fontName="Helvetica-Bold",
        )
        totaux_rows.append(
            [Paragraph("Crédit de ce bon :", totaux_label), Paragraph(fmt_currency(credit_bon), p_credit_bon)]
        )

    # Ancien Solde du client (affiché si client enregistré ou ancien != 0)
    if not is_passager or ancien != Decimal("0.00"):
        if ancien < -Decimal("0.009"):
            p_anc_val = ParagraphStyle("AncVal", parent=totaux_val, textColor=colors.HexColor("#dc2626"))
            totaux_rows.append(
                [Paragraph("Ancien solde (Dette) :", totaux_label), Paragraph(fmt_currency(abs(ancien)), p_anc_val)]
            )
        elif ancien > Decimal("0.009"):
            p_anc_val = ParagraphStyle("AncVal", parent=totaux_val, textColor=colors.HexColor("#16a34a"))
            totaux_rows.append(
                [Paragraph("Ancien solde (Avoir) :", totaux_label), Paragraph(fmt_currency(ancien), p_anc_val)]
            )
        else:
            totaux_rows.append(
                [Paragraph("Ancien solde :", totaux_label), Paragraph("0,00 DA", totaux_val)]
            )

    # Nouveau Solde du client (affiché si client enregistré ou nouveau != 0)
    if not is_passager or nouveau != Decimal("0.00"):
        if nouveau < -Decimal("0.009"):
            p_nouv_val = ParagraphStyle(
                "NouvDetteVal",
                parent=totaux_val,
                textColor=colors.HexColor("#dc2626"),
                fontName="Helvetica-Bold",
                fontSize=9.5,
            )
            totaux_rows.append(
                [Paragraph("Nouveau solde (Il nous doit) :", totaux_label), Paragraph(fmt_currency(abs(nouveau)), p_nouv_val)]
            )
        elif nouveau > Decimal("0.009"):
            p_nouv_val = ParagraphStyle(
                "NouvAvoirVal",
                parent=totaux_val,
                textColor=colors.HexColor("#16a34a"),
                fontName="Helvetica-Bold",
                fontSize=9.5,
            )
            totaux_rows.append(
                [Paragraph("Nouveau solde (Avoir client) :", totaux_label), Paragraph(fmt_currency(nouveau), p_nouv_val)]
            )
        else:
            p_nouv_val = ParagraphStyle(
                "NouvSoldeOk",
                parent=totaux_val,
                textColor=colors.HexColor("#334155"),
                fontName="Helvetica-Bold",
            )
            totaux_rows.append(
                [Paragraph("Nouveau solde :", totaux_label), Paragraph("0,00 DA (Réglé)", p_nouv_val)]
            )

    table_totaux = Table(
        totaux_rows,
        colWidths=[48 * mm, 42 * mm],
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ],
    )

    footer_text = [
        Paragraph("Document délivré par le logiciel de caisse LOGISZ.", store_meta),
        Paragraph("Les marchandises vendues ne sont ni reprises ni échangées après 48h.", store_meta),
        Paragraph("Merci pour votre confiance !", ParagraphStyle("Merci", parent=store_meta, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"))),
    ]

    try:
        clean_code = "".join(c for c in str(n_bon) if c.isalnum())
        if clean_code:
            barcode = code128.Code128(clean_code, barHeight=6 * mm, barWidth=1.0)
            footer_text.append(Spacer(1, 1 * mm))
            footer_text.append(barcode)
    except Exception:
        pass

    lower_table = Table(
        [[footer_text, table_totaux]],
        colWidths=[100 * mm, 90 * mm],
        style=[
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ],
    )
    story.append(lower_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
