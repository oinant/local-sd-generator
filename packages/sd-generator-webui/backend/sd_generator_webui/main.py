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


def get_frontend_path() -> Path | None:
    """
    Locate frontend build directory.

    Priority:
    1. Monorepo dev: backend/static/dist (sibling to sd_generator_webui module)
    2. Pip install: site-packages/backend/static/dist

    Returns:
        Path to frontend dist directory or None if not found
    """
    # Get backend package directory (where this file is)
    # This is: .../backend/sd_generator_webui/
    package_dir = Path(__file__).parent

    # Try 1: Monorepo dev - go up to backend/, then static/dist
    # From: .../backend/sd_generator_webui/
    # To:   .../backend/static/dist
    backend_dir = package_dir.parent
    frontend_dist = backend_dir / "static" / "dist"
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        return frontend_dist

    # Try 2: Pip install - frontend in site-packages/backend/static/dist
    # package_dir = .../site-packages/sd_generator_webui
    # backend_dir = .../site-packages/backend
    site_packages = package_dir.parent
    backend_dist = site_packages / "backend" / "static" / "dist"
    if backend_dist.exists() and (backend_dist / "index.html").exists():
        return backend_dist

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
            print("✓ Backend sert le frontend à /webui")
            app.state.frontend_path = frontend_path
            app.state.production_mode = True

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
    """API info page - redirects to /webui in production."""
    if app.state.production_mode and app.state.frontend_path:
        # Production mode: redirect to /webui
        return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SD Image Generator</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="0;url=/webui">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; text-align: center; }
            .container { max-width: 600px; margin: 100px auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            a { color: #007bff; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 SD Image Generator</h1>
            <p>Redirecting to <a href="/webui">/webui</a>...</p>
            <p><small>API docs: <a href="/docs">/docs</a></small></p>
        </div>
    </body>
    </html>
    """)

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


# WebUI routes - serve frontend at /webui
@app.get("/webui")
async def serve_webui_root():
    """Serve WebUI index.html at /webui."""
    if not app.state.production_mode:
        raise HTTPException(
            status_code=404,
            detail="WebUI not available in dev mode. Use --dev-mode flag with separate Vite server on http://localhost:5173"
        )

    if not app.state.frontend_path:
        raise HTTPException(
            status_code=500,
            detail="Frontend build not found. Server misconfiguration: run 'npm run build' in front/ directory and rebuild package."
        )

    index_file = app.state.frontend_path / "index.html"
    return FileResponse(index_file)


@app.get("/webui/{full_path:path}")
async def serve_webui_spa(full_path: str):
    """
    Catch-all for SPA routing under /webui.
    Serves static files if they exist, otherwise serves index.html for Vue Router.
    """
    if not app.state.production_mode:
        raise HTTPException(
            status_code=404,
            detail="WebUI not available in dev mode. Use --dev-mode flag with separate Vite server on http://localhost:5173"
        )

    if not app.state.frontend_path:
        raise HTTPException(
            status_code=500,
            detail="Frontend build not found. Server misconfiguration: run 'npm run build' in front/ directory and rebuild package."
        )

    # Check if requested file exists (js, css, fonts, img, etc.)
    requested_file = app.state.frontend_path / full_path
    if requested_file.exists() and requested_file.is_file():
        return FileResponse(requested_file)

    # Otherwise serve index.html for Vue Router (client-side routing)
    index_file = app.state.frontend_path / "index.html"
    return FileResponse(index_file)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )