from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from config import API_HOST, API_PORT
from api import images, auth, files  # generation temporairement désactivé (imports CLI manquants)
from __about__ import __version__


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application."""
    # Startup
    print("🚀 Démarrage du backend SD Image Generator")

    yield

    # Shutdown
    print("🔄 Arrêt du backend SD Image Generator")


# Créer l'application FastAPI
app = FastAPI(
    title="SD Image Generator Backend",
    description="Backend web moderne pour la génération d'images Stable Diffusion",
    version=__version__,
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclure les routeurs API
app.include_router(auth.router)
app.include_router(images.router)
# app.include_router(generation.router)  # TODO: Via queue background jobs (Celery) pour sécurité
app.include_router(files.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Page d'accueil simple."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SD Image Generator</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
            .get { background: #28a745; color: white; }
            .post { background: #007bff; color: white; }
            code { background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 SD Image Generator Backend</h1>
            <p>Backend web moderne pour la génération d'images Stable Diffusion</p>

            <h2>📚 Documentation API</h2>
            <p>Accédez à la documentation interactive : <a href="/docs">/docs</a></p>

            <h2>🔗 Endpoints principaux</h2>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/images</code> - Liste les images avec pagination
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/images/{filename}</code> - Récupère une image (+ paramètre ?thumbnail=true)
            </div>

            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/generation</code> - Lance une nouvelle génération
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/generation/{job_id}</code> - Statut d'une génération
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/auth/me</code> - Informations utilisateur
            </div>

            <h2>🔐 Authentification</h2>
            <p>Utilisez un token Bearer avec un GUID valide dans l'en-tête Authorization :</p>
            <code>Authorization: Bearer 550e8400-e29b-41d4-a716-446655440000</code>

            <h2>📊 Version</h2>
            <p>Version actuelle : <strong>""" + __version__ + """</strong></p>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Point de contrôle de santé."""
    return {
        "status": "healthy",
        "version": __version__,
        "service": "sd-image-generator-backend"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )