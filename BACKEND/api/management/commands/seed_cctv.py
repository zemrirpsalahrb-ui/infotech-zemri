from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from api.models import (
    CustomerProfile,
    Category,
    Brand,
    Product,
    ProductImage,
    Banner,
    Review,
)


class Command(BaseCommand):
    help = "Seeds the CCTV e-commerce database with categories, brands, accounts, banners, and initial products."

    def handle(self, *args, **options):
        # 1. All 13 Mandatory CCTV Categories
        categories_data = [
            ("IP Cameras", "Camera", "Caméras réseau IP PoE haute définition 2MP, 4MP, 8MP 4K avec IA AcuSense / WizSense."),
            ("Wi-Fi Cameras", "Wifi", "Caméras sans-fil Wi-Fi intelligentes motorisées 360° intérieur et extérieur."),
            ("Analog Cameras", "Video", "Caméras HDCVI / HDTVI / AHD 1080p et 5MP longue portée IR et ColorVu / Full-Color."),
            ("PTZ Cameras", "Compass", "Dômes motorisés PTZ zoom optique x25/x32 avec suivi automatique."),
            ("DVR", "HardDrive", "Enregistreurs numériques XVR / DVR Penta-brid 4, 8, 16 et 32 canaux H.265+."),
            ("NVR", "Server", "Enregistreurs réseau IP NVR 4K PoE intégré pour architectures IP professionnelles."),
            ("Surveillance Hard Drives", "Database", "Disques durs certifiés vidéosurveillance 24/7 WD Purple et Seagate SkyHawk."),
            ("Power Supplies", "Zap", "Blocs d'alimentation stabilisés 12V 4S/8S/16S, chargeurs 12V 2A et switches PoE."),
            ("Cables", "Cable", "Bobines de câble coaxial RG59+2C, Cat6 UTP/FTP cuivre pur et câbles HDMI 4K."),
            ("Connectors", "Plug", "Fiches BNC à sertir/visser, vidéo baluns passifs/actifs, connecteurs DC et RJ45."),
            ("Alarm Systems", "ShieldAlert", "Systèmes d'alarme anti-intrusion sans-fil et filaires, détecteurs PIR et sirènes."),
            ("Accessories", "Box", "Boîtes de jonction étanches IP66, supports muraux, splitters, répéteurs KVM."),
            ("Complete CCTV Kits", "PackageCheck", "Packs vidéosurveillance complets prêts à installer (Caméras + XVR/NVR + HDD + Accessoires)."),
        ]
        cat_map = {}
        for idx, (name, icon, desc) in enumerate(categories_data):
            cat, _ = Category.objects.update_or_create(
                name=name,
                defaults={"icon_name": icon, "description": desc, "sort_order": idx + 1, "is_active": True},
            )
            cat_map[name] = cat

        # 2. Brands
        brands_data = [
            ("Dahua Technology", "Leader mondial des solutions HDCVI, XVR WizSense et caméras Full-Color."),
            ("Hikvision", "Solutions de vidéosurveillance IP, Turbo HD, ColorVu et AcuSense."),
            ("EZVIZ", "Caméras Wi-Fi intelligentes et sécurité connectée résidentielle."),
            ("IMOU", "Caméras Wi-Fi Cruiser, Ranger et projecteurs de sécurité Smart."),
            ("Western Digital", "Disques durs WD Purple optimisés AllFrame pour vidéosurveillance 24/7."),
            ("Uniview (UNV)", "Architecture IP NVR et caméras professionnelles LightHunter."),
            ("LOGISZ PRO", "Accessoires professionnels certifiés : alimentations, boîtes de jonction, connectique et KVM."),
        ]
        brand_map = {}
        for idx, (bname, bdesc) in enumerate(brands_data):
            b, _ = Brand.objects.update_or_create(
                name=bname,
                defaults={"description": bdesc, "sort_order": idx + 1, "is_featured": True},
            )
            brand_map[bname] = b

        # 3. Banners
        Banner.objects.update_or_create(
            title="Architecture de Sécurité & Vidéosurveillance Pro",
            defaults={
                "subtitle": "Équipez vos chantiers, entreprises et résidences avec nos systèmes CCTV certifiés. Tarifs dédiés Installateurs & Revendeurs.",
                "badge_text": "SYNCHRONISÉ EN TEMPS RÉEL • STOCK OFFICIEL",
                "cta_text": "Configurer un Kit sur mesure",
                "cta_link": "/kit-builder",
                "accent_color": "#3B82F6",
                "sort_order": 1,
                "is_active": True,
            },
        )
        Banner.objects.update_or_create(
            title="Programme Partenaires : Installateurs & Revendeurs",
            defaults={
                "subtitle": "Ouvrez votre compte professionnel et accédez instantanément aux grilles tarifaires Gros et Installateur après validation.",
                "badge_text": "TARIFS B2B PRIVILÉGIÉS",
                "cta_text": "Demander un compte Pro",
                "cta_link": "/account",
                "accent_color": "#0EA5E9",
                "sort_order": 2,
                "is_active": True,
            },
        )

        # 4. Accounts (Admin, Approved Installer, Pending Installer, Approved Reseller)
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@logisz-security.dz", "is_staff": True, "is_superuser": True, "first_name": "Admin", "last_name": "LOGISZ"},
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("admin123")
        admin_user.save()
        CustomerProfile.objects.update_or_create(
            user=admin_user,
            defaults={"account_type": "ADMIN", "requested_type": "ADMIN", "approval_status": "APPROVED", "company_name": "LOGISZ HQ", "phone": "+213550000000"},
        )

        inst_user, _ = User.objects.get_or_create(
            username="installateur_pro",
            defaults={"email": "installateur@cctv-dz.com", "first_name": "Karim", "last_name": "Installateur"},
        )
        inst_user.set_password("pro12345")
        inst_user.save()
        CustomerProfile.objects.update_or_create(
            user=inst_user,
            defaults={
                "account_type": "INSTALLER",
                "requested_type": "INSTALLER",
                "approval_status": "APPROVED",
                "company_name": "Karim Sécurité Installation",
                "phone": "0551223344",
                "wilaya": "Alger",
                "rc_number": "16/00-445512B",
            },
        )

        pend_user, _ = User.objects.get_or_create(
            username="installateur_attente",
            defaults={"email": "pending@cctv-dz.com", "first_name": "Yacine", "last_name": "Tech"},
        )
        pend_user.set_password("pro12345")
        pend_user.save()
        CustomerProfile.objects.update_or_create(
            user=pend_user,
            defaults={
                "account_type": "INSTALLER",
                "requested_type": "INSTALLER",
                "approval_status": "PENDING",
                "company_name": "Yacine Réseaux & Caméras",
                "phone": "0661998877",
                "wilaya": "Oran",
                "professional_justification": "Installateur spécialisé courant faible depuis 5 ans.",
            },
        )

        res_user, _ = User.objects.get_or_create(
            username="revendeur_gros",
            defaults={"email": "revendeur@cctv-dz.com", "first_name": "Sofiane", "last_name": "Distribution"},
        )
        res_user.set_password("gros12345")
        res_user.save()
        CustomerProfile.objects.update_or_create(
            user=res_user,
            defaults={
                "account_type": "RESELLER",
                "requested_type": "RESELLER",
                "approval_status": "APPROVED",
                "company_name": "SARL Sofiane CCTV Distribution",
                "phone": "0770112233",
                "wilaya": "Sétif",
                "rc_number": "19/01-998877A",
                "nif_number": "001919099887744",
            },
        )

        # 5. Core CCTV Products matching actual desktop references in inventair
        sample_products = [
            {
                "desktop_ide": 1,
                "reference": "9L11FB1P",
                "name": "T1A21P - Caméra Dôme HDCVI 2MP IR 20m Cooper",
                "category": cat_map["Analog Cameras"],
                "brand": brand_map["Dahua Technology"],
                "public_price": Decimal("4500.00"),
                "installer_price": Decimal("4150.00"),
                "reseller_price": Decimal("3900.00"),
                "promo_price": Decimal("4290.00"),
                "physical_stock": Decimal("45.00"),
                "kit_component_type": "CAMERA",
                "kit_technology": "ANALOG_HD",
                "is_featured": True,
                "is_bestseller": True,
                "short_description": "Caméra dôme 4-en-1 Full HD 1080p (CVI/TVI/AHD/CVBS) avec vision nocturne Smart IR 20m.",
                "description": "La caméra Dahua Cooper T1A21P offre une vidéosurveillance Full HD 1080p fiable à haute sensibilité nocturne. Compatible avec tous les enregistreurs XVR/DVR.",
                "technical_specs": {
                    "Résolution": "2 MP (1920 × 1080) @ 30 fps",
                    "Objectif": "2.8 mm grand angle (103°)",
                    "Vision nocturne": "Smart IR jusqu'à 20 mètres",
                    "Sortie vidéo": "4-en-1 commutable HDCVI / TVI / AHD / CVBS",
                    "Alimentation": "12V DC ±30% (Max 2.7W)",
                },
                "image": "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 27,
                "reference": "125046",
                "name": "XVR 4CH 5MP WizSense H.265+ Penta-brid",
                "category": cat_map["DVR"],
                "brand": brand_map["Dahua Technology"],
                "public_price": Decimal("14500.00"),
                "installer_price": Decimal("13900.00"),
                "reseller_price": Decimal("13500.00"),
                "physical_stock": Decimal("18.00"),
                "kit_component_type": "RECORDER",
                "kit_technology": "ANALOG_HD",
                "kit_channels": 4,
                "is_featured": True,
                "is_bestseller": True,
                "short_description": "Enregistreur numérique 4 canaux 5M-N avec compression AI Coding H.265+ et détection SMD Plus.",
                "description": "Enregistreur XVR 4 canaux supportant les caméras HDCVI, AHD, TVI, CVBS et caméras IP additionnelles jusqu'à 6MP. Idéal pour commerces et villas.",
                "technical_specs": {
                    "Canaux": "4 canaux BNC + 2 canaux IP (jusqu'à 6MP)",
                    "Compression": "AI Coding / Smart H.265+ / H.265",
                    "Sortie vidéo": "HDMI & VGA simultanés 1080p",
                    "Stockage": "1 port SATA jusqu'à 16 TB",
                    "Application mobile": "DMSS (iOS & Android)",
                },
                "image": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 46,
                "reference": "P000046",
                "name": "XVR 8CH I3 - Enregistreur 8 Canaux AI AcuSense / WizSense",
                "category": cat_map["DVR"],
                "brand": brand_map["Hikvision"],
                "public_price": Decimal("20500.00"),
                "installer_price": Decimal("19500.00"),
                "reseller_price": Decimal("19000.00"),
                "physical_stock": Decimal("12.00"),
                "kit_component_type": "RECORDER",
                "kit_technology": "ANALOG_HD",
                "kit_channels": 8,
                "is_featured": True,
                "is_new_arrival": True,
                "short_description": "Enregistreur 8 canaux intelligent avec filtrage humain/véhicule et sortie HDMI 4K.",
                "description": "Solution d'enregistrement haute performance 8 canaux avec intelligence artificielle intégrée réduisant les fausses alarmes.",
                "technical_specs": {
                    "Canaux": "8 canaux analogiques HD + 4 canaux IP",
                    "Intelligence Artificielle": "Détection cible Humain / Véhicule 2.0",
                    "Compression": "H.265 Pro+ / H.265 Pro",
                    "Disque dur": "1 interface SATA (jusqu'à 10 TB)",
                },
                "image": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 30,
                "reference": "P000030",
                "name": "XVR 16CH 5MP - Enregistreur 16 Canaux Haute Capacité",
                "category": cat_map["DVR"],
                "brand": brand_map["Dahua Technology"],
                "public_price": Decimal("27000.00"),
                "installer_price": Decimal("26500.00"),
                "reseller_price": Decimal("26000.00"),
                "physical_stock": Decimal("8.00"),
                "kit_component_type": "RECORDER",
                "kit_technology": "ANALOG_HD",
                "kit_channels": 16,
                "is_featured": True,
                "short_description": "Enregistreur professionnel 16 canaux 5M-N pour grandes installations industrielles et commerciales.",
                "description": "Architecture 16 canaux robuste avec bande passante étendue, audio sur coaxial et gestion multi-écrans.",
                "technical_specs": {
                    "Canaux": "16 canaux BNC + jusqu'à 8 canaux IP",
                    "Résolution max": "5M-N / 4M-N / 1080P",
                    "Sorties vidéo": "HDMI 4K + VGA",
                    "Audio": "Audio sur câble coaxial (AOC) sur les 16 canaux",
                },
                "image": "https://images.unsplash.com/photo-1597852074816-d933c7d2b988?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 45,
                "reference": "120365",
                "name": "DISQUE DURE 4 TB PERPEL - WD Purple Surveillance 24/7",
                "category": cat_map["Surveillance Hard Drives"],
                "brand": brand_map["Western Digital"],
                "public_price": Decimal("29500.00"),
                "installer_price": Decimal("28500.00"),
                "reseller_price": Decimal("27900.00"),
                "physical_stock": Decimal("15.00"),
                "kit_component_type": "HDD",
                "kit_technology": "ALL",
                "is_featured": True,
                "is_bestseller": True,
                "short_description": "Disque dur 4 To Western Digital Purple conçu exclusivement pour les systèmes NVR et DVR fonctionnant 24h/24 et 7j/7.",
                "description": "Doté de la technologie exclusive AllFrame, le disque WD Purple 4 TB élimine les pertes d'images et supporte jusqu'à 64 caméras HD en flux continu.",
                "technical_specs": {
                    "Capacité": "4 To (4000 Go)",
                    "Interface": "SATA III 6 Gb/s - Format 3.5 pouces",
                    "Technologie": "WD AllFrame 4K Surveillance",
                    "Charge nominale": "180 To / an - Fonctionnement continu 24/7",
                    "Cache": "256 Mo",
                },
                "image": "https://images.unsplash.com/photo-1531492746076-161ca9bcad58?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 7,
                "reference": "6975254100025",
                "name": "DISQUE DURE 500 GB - Stockage Vidéosurveillance",
                "category": cat_map["Surveillance Hard Drives"],
                "brand": brand_map["Western Digital"],
                "public_price": Decimal("5000.00"),
                "installer_price": Decimal("4300.00"),
                "reseller_price": Decimal("4000.00"),
                "physical_stock": Decimal("32.00"),
                "kit_component_type": "HDD",
                "kit_technology": "ALL",
                "short_description": "Disque dur SATA 500 Go économique pour enregistreurs DVR 4 canaux.",
                "description": "Solution de stockage fiable et accessible pour les petites installations de 2 à 4 caméras.",
                "technical_specs": {
                    "Capacité": "500 Go",
                    "Interface": "SATA 3.5 pouces",
                    "Usage": "Enregistrement continu DVR / XVR",
                },
                "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 34,
                "reference": "P000034",
                "name": "BLOC ALIMENTATION 4S - Alimentation Stabilisée 12V 4 Sorties",
                "category": cat_map["Power Supplies"],
                "brand": brand_map["LOGISZ PRO"],
                "public_price": Decimal("2500.00"),
                "installer_price": Decimal("2200.00"),
                "reseller_price": Decimal("2000.00"),
                "physical_stock": Decimal("60.00"),
                "kit_component_type": "PSU",
                "kit_technology": "ALL",
                "is_bestseller": True,
                "short_description": "Alimentation centralisée 12V DC à 4 sorties protégées contre les surtensions et courts-circuits.",
                "description": "Alimentez jusqu'à 4 caméras de surveillance avec une tension régulée 12V DC propre pour éviter tout parasite vidéo.",
                "technical_specs": {
                    "Tension de sortie": "12V DC régulée",
                    "Sorties": "4 canaux indépendants protégés PTC",
                    "Protection": "Court-circuit, surcharge et surtension",
                },
                "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 58,
                "reference": "123540",
                "name": "CHARGEUR 12V 2A - Alimentation Individuelle Caméra",
                "category": cat_map["Power Supplies"],
                "brand": brand_map["LOGISZ PRO"],
                "public_price": Decimal("500.00"),
                "installer_price": Decimal("420.00"),
                "reseller_price": Decimal("400.00"),
                "physical_stock": Decimal("180.00"),
                "kit_component_type": "PSU",
                "kit_technology": "ALL",
                "short_description": "Adaptateur secteur 12V 2A haute stabilité avec connecteur DC 5.5x2.1mm.",
                "description": "Bloc secteur individuel 12V 2A filtré anti-interférences pour caméra ou routeur.",
                "technical_specs": {"Sortie": "12V DC - 2.0 Ampères", "Connecteur": "DC 5.5 × 2.1 mm"},
                "image": "https://images.unsplash.com/photo-1585338107529-13afc5f02586?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 31,
                "reference": "6131860480719",
                "name": "BNC - Connecteur BNC Professionnel Coaxial",
                "category": cat_map["Connectors"],
                "brand": brand_map["LOGISZ PRO"],
                "public_price": Decimal("50.00"),
                "installer_price": Decimal("42.00"),
                "reseller_price": Decimal("40.00"),
                "physical_stock": Decimal("500.00"),
                "kit_component_type": "CONNECTOR",
                "kit_technology": "ANALOG_HD",
                "short_description": "Connecteur BNC métal haute conductivité pour câble coaxial RG59 / KX6.",
                "description": "Assure une transmission vidéo HD sans perte ni atténuation sur vos liaisons coaxiales.",
                "technical_specs": {"Impédance": "75 Ohms", "Compatibilité": "RG59 / RG6 / KX6"},
                "image": "https://images.unsplash.com/photo-1544724569-5f546fd6f2b5?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 33,
                "reference": "P000033",
                "name": "JONCTION 0501 PRO - Boîte de Dérivation Étanche Caméra",
                "category": cat_map["Accessories"],
                "brand": brand_map["LOGISZ PRO"],
                "public_price": Decimal("300.00"),
                "installer_price": Decimal("270.00"),
                "reseller_price": Decimal("250.00"),
                "physical_stock": Decimal("220.00"),
                "kit_component_type": "ACCESSORY",
                "kit_technology": "ALL",
                "short_description": "Boîte de jonction étanche IP66 pour protéger vos connecteurs BNC, RJ45 et DC en extérieur.",
                "description": "Indispensable pour une finition professionnelle et une protection durable contre la pluie et la poussière.",
                "technical_specs": {"Indice": "IP66 extérieur/intérieur", "Matériau": "ABS anti-UV haute résistance"},
                "image": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 24,
                "reference": "P000024",
                "name": "HDMI 4K 10M BOX - Câble HDMI Ultra HD 4K Blindé 10 Mètres",
                "category": cat_map["Cables"],
                "brand": brand_map["LOGISZ PRO"],
                "public_price": Decimal("2400.00"),
                "installer_price": Decimal("2200.00"),
                "reseller_price": Decimal("2100.00"),
                "physical_stock": Decimal("40.00"),
                "kit_component_type": "CABLE",
                "kit_technology": "ALL",
                "short_description": "Câble HDMI 2.0 4K 10m triple blindage pour relier vos XVR/NVR aux moniteurs de contrôle.",
                "description": "Conçu pour transmettre un signal 4K UHD stable sur 10 mètres sans perte de signal.",
                "technical_specs": {"Longueur": "10 mètres", "Résolution": "4K Ultra HD 60Hz", "Connecteurs": "Plaqués or"},
                "image": "https://images.unsplash.com/photo-1601524909162-ae8725290836?auto=format&fit=crop&w=900&q=80",
            },
            {
                "desktop_ide": 16,
                "reference": "0123654",
                "name": "KVM 60M - Extendeur HDMI + Souris USB sur Câble RJ45 (60m)",
                "category": cat_map["Accessories"],
                "brand": brand_map["LOGISZ PRO"],
                "public_price": Decimal("8500.00"),
                "installer_price": Decimal("7800.00"),
                "reseller_price": Decimal("7500.00"),
                "promo_price": Decimal("7990.00"),
                "physical_stock": Decimal("25.00"),
                "kit_component_type": "ACCESSORY",
                "kit_technology": "ALL",
                "is_featured": True,
                "is_special_offer": True,
                "short_description": "Déportez l'affichage HDMI 1080p et la souris USB de votre DVR/NVR jusqu'à 60 mètres via un simple câble Cat6.",
                "description": "L'extendeur KVM 60M permet de contrôler votre enregistreur DVR ou NVR à distance depuis un bureau ou poste de garde via un câble réseau RJ45 unique.",
                "technical_specs": {
                    "Portée": "Jusqu'à 60 mètres sur câble Cat6",
                    "Signal": "HDMI 1080p @ 60Hz + USB (Souris/Clavier)",
                    "Contenu": "Émetteur (TX) + Récepteur (RX) + Alimentations",
                },
                "image": "https://images.unsplash.com/photo-1563770660941-20978e870e26?auto=format&fit=crop&w=900&q=80",
            },
        ]

        now = timezone.now()
        for pdata in sample_products:
            img_url = pdata.pop("image")
            prod, _ = Product.objects.update_or_create(
                reference=pdata["reference"],
                defaults={**pdata, "last_desktop_sync": now, "is_active": True},
            )
            if not prod.images.exists():
                ProductImage.objects.create(
                    product=prod,
                    image_url=img_url,
                    alt_text=prod.name,
                    is_main=True,
                    sort_order=1,
                )

        # Add approved reviews
        first_prod = Product.objects.filter(reference="9L11FB1P").first()
        if first_prod and not first_prod.reviews.exists():
            Review.objects.create(
                product=first_prod,
                author_name="Karim B. (Installateur Agréé)",
                rating=5,
                title="Excellente qualité d'image jour et nuit",
                comment="Installée sur plus de 20 chantiers cette année. Zéro retour SAV et très bonne portée IR la nuit.",
                is_verified_purchase=True,
                status="APPROVED",
                admin_reply="Merci pour votre fidélité Karim ! Le stock est disponible en continu.",
            )

        self.stdout.write(self.style.SUCCESS("CCTV database seeded successfully!"))

