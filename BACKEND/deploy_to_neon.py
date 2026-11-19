"""
Script de migration et synchronisation automatique vers Neon PostgreSQL.
Utilisation :
    python deploy_to_neon.py "postgresql://user:password@ep-xyz.region.aws.neon.tech/neondb?sslmode=require"
ou
    python deploy_to_neon.py (lit DATABASE_URL dans BACKEND/.env)
"""
import os
import sys
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))

neon_url = None
if len(sys.argv) > 1 and sys.argv[1].startswith("postgres"):
    neon_url = sys.argv[1]
else:
    # Read from .env
    env_path = os.path.join(BASE, '.env')
    if os.path.exists(env_path):
        for line in open(env_path, encoding='utf-8'):
            if line.startswith('DATABASE_URL='):
                val = line.strip().split('=', 1)[1].strip()
                if val.startswith('postgres') and not 'YOUR_NEON_PASSWORD' in val:
                    neon_url = val

if not neon_url:
    print("=" * 70)
    print("CONFIGURATION NEON POSTGRESQL REQUISE")
    print("=" * 70)
    print("Pour migrer votre base de donnees vers Neon :")
    print("1. Creez un projet gratuit sur https://neon.tech")
    print("2. Copiez votre chaine de connexion (Connection String)")
    print("3. Lancez la commande suivante :")
    print("   python deploy_to_neon.py \"postgresql://votre_user:votre_mot_de_passe@ep-xyz.region.aws.neon.tech/neondb?sslmode=require\"")
    print("=" * 70)
    sys.exit(0)

print(f"Connexion a Neon PostgreSQL : {neon_url[:35]}...")

dump_file = os.path.join(BASE, 'catalog_data.json')
print("1. Exportation des donnees du catalogue local (SQLite -> JSON)...")
# Dump local data using sqlite without DATABASE_URL in environment
env_local = os.environ.copy()
env_local.pop('DATABASE_URL', None)
ret = subprocess.run([sys.executable, 'manage.py', 'dumpdata', 'api', '--indent', '2', '--output', dump_file],
                     cwd=BASE, env=env_local)
if ret.returncode != 0:
    print("Erreur lors de l'export des donnees locales.")
    sys.exit(1)
print(f" -> Donnees exportees avec succes dans {dump_file} !")

print("2. Application des migrations Django sur Neon PostgreSQL...")
env_neon = os.environ.copy()
env_neon['DATABASE_URL'] = neon_url
ret = subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'],
                     cwd=BASE, env=env_neon)
if ret.returncode != 0:
    print("Erreur lors des migrations sur Neon.")
    sys.exit(1)
print(" -> Migrations terminees avec succes !")

print("3. Importation des donnees vers Neon PostgreSQL...")
ret = subprocess.run([sys.executable, 'manage.py', 'loaddata', dump_file],
                     cwd=BASE, env=env_neon)
if ret.returncode != 0:
    print("Erreur lors du chargement des donnees sur Neon.")
    sys.exit(1)

print("=" * 70)
print("SUCCÈS : VOTRE BASE NEON POSTGRESQL EST PRÊTE ET 100% SYNCHRONISÉE !")
print(f"URL de connexion Neon : {neon_url[:35]}...")
print("Vous pouvez maintenant renseigner ce DATABASE_URL sur Render.")
print("=" * 70)


