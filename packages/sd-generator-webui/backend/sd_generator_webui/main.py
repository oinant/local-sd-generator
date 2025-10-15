from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

from sd_generator_webui.config import API_HOST, API_PORT
from sd_generator_webui.api import images, auth, files, sessions  # generation temporairement désactivé (imports CLI manquants)
from sd_generator_webui.__about__ import __version__


def get_frontend_path() -> Path:
    """
    Locate frontend build directory.

    Priority:
    1. Packaged build (production): ../front/dist
    2. Monorepo dev mode: ../../front/dist

    Returns:
        Path to frontend dist directory or None if not found
    """
    # Get package root
    package_root = Path(__file__).parent.parent.parent

    # Try packaged build (production)
    frontend_dist = package_root / "front" / "dist"
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        return frontend_dist

    # Try monorepo structure (dev mode - but frontend must be built)
    monorepo_dist = package_root.parent.parent / "front" / "dist"
    if monorepo_dist.exists() and (monorepo_dist / "index.html").exists():
        return monorepo_dist

    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application."""
    # Startup
    print("🚀 Démarrage du backend SD Image Generator")

    # Check if we're in dev mode (explicit flag from CLI)
    dev_mode_env = os.environ.get("SD_GENERATOR_DEV_MODE")
    print(f"DEBUG: SD_GENERATOR_DEV_MODE = {dev_mode_env}")
    dev_mode = dev_mode_env == "1"

    if dev_mode:
        # DEV MODE: Frontend runs on separate Vite dev server
        print("✓ Mode DEV (explicit flag)")
        print("✓ Frontend attendu sur http://localhost:5173 (Vite dev server)")
        app.state.frontend_path = None
        app.state.production_mode = False

    else:
        # PRODUCTION MODE: Backend serves built frontend
        print("✓ Mode PRODUCTION (default)")
        frontend_path = get_frontend_path()

        if frontend_path:
            print(f"✓ Frontend build trouvé: {frontend_path}")
            print("✓ Backend sert le frontend static")
            app.state.frontend_path = frontend_path
            app.state.production_mode = True

            # Mount static files
            try:
                app.mount(
                    "/assets",
                    StaticFiles(directory=str(frontend_path / "assets")),
                    name="assets"
                )
                print("✓ Assets montés: /assets")
            except Exception as e:
                print(f"⚠ Erreur montage assets: {e}")

        else:
            print("⚠ Pas de frontend build - Backend API only")
            app.state.frontend_path = None
            app.state.production_mode = True  # Still production, just no frontend

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

# Configuration CORS (pour mode dev avec Vite séparé)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routeurs API
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(images.router)
# app.include_router(generation.router)  # TODO: Via queue background jobs (Celery) pour sécurité
app.include_router(files.router)


@app.get("/api/mode")
async def get_mode():
    """Return current mode (dev/production)."""
    return {
        "mode": "production" if app.state.production_mode else "dev",
        "frontend_path": str(app.state.frontend_path) if app.state.frontend_path else None
    }


@app.get("/")
async def root():
    """
    Serve frontend in production mode or API info page in dev mode.
    """
    # Production mode: serve frontend build
    if app.state.production_mode and app.state.frontend_path:
        index_file = app.state.frontend_path / "index.html"
        return FileResponse(index_file)

    # Dev mode: show API info page
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SD Image Generator - Dev Mode</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .dev-banner { background: #ffc107; color: #000; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; font-weight: bold; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
            .get { background: #28a745; color: white; }
            .post { background: #007bff; color: white; }
            code { background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="dev-banner">⚠️ MODE DÉVELOPPEMENT - Frontend séparé attendu sur http://localhost:5173</div>

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
                <code>/api/images/{filename}</code> - Récupère une image
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/auth/me</code> - Informations utilisateur
            </div>

            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/mode</code> - Mode actuel (dev/production)
            </div>

            <h2>🔐 Authentification</h2>
            <p>Utilisez un token Bearer avec un GUID valide dans l'en-tête Authorization.</p>

            <h2>📊 Version</h2>
            <p>Version actuelle : <strong>""" + __version__ + """</strong></p>

            <h2>🛠️ Mode Dev</h2>
            <p>Frontend: Lancez <code>npm run dev</code> dans le dossier <code>front/</code></p>
            <p>Backend: Ce serveur FastAPI (port 8000)</p>
        </div>
    </body>
    </html>
    """)


@app.get("/health")
async def health_check():
    """Point de contrôle de santé."""
    return {
        "status": "healthy",
        "version": __version__,
        "service": "sd-image-generator-backend"
    }


# Catch-all route for SPA (Vue Router) - MUST BE LAST
# This handles client-side routing (e.g., /gallery, /login, etc.)
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """
    Catch-all for SPA routing in production mode.
    In dev mode, returns 404.
    """
    # Production mode: serve index.html for all non-API routes
    if app.state.production_mode and app.state.frontend_path:
        # Don't catch API routes
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("health"):
            raise HTTPException(status_code=404, detail="Not found")

        index_file = app.state.frontend_path / "index.html"
        return FileResponse(index_file)

    # Dev mode: 404
    raise HTTPException(status_code=404, detail="Not found - use frontend dev server")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )