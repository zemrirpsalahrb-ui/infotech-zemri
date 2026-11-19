@echo off
chcp 65001 >nul
title Migration Neon PostgreSQL - INFOTECH ZEMRI
echo ======================================================================
echo          MIGRATION DU SITE ET CATALOGUE VERS NEON POSTGRESQL
echo ======================================================================
echo.
echo 1. Connectez-vous sur https://neon.tech et creez un projet (gratuit).
echo 2. Copiez la chaine de connexion "Connection Details" (postgresql://...)
echo.
set /p NEON_URL="Collez ici votre lien de connexion Neon : "
if "%NEON_URL%"=="" (
    echo.
    echo [ERREUR] Aucun lien fourni. Operation annulee.
    echo.
    pause
    exit /b 1
)

echo.
echo Connexion a Neon et synchronisation des 497 produits et photos...
echo.
cd /d "c:\Users\asus\Desktop\logicielle\BACKEND"
python deploy_to_neon.py "%NEON_URL%"

echo.
pause
