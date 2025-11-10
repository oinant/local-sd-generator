# Thumbnail Watchdog - Architecture & Optimizations

## Vue d'ensemble

Le **Thumbnail Watchdog** génère automatiquement des thumbnails WebP à partir des images PNG générées par `sdgen generate`.

**Fonctionnalités clés :**
- ✅ **Smart catchup** - Traite uniquement les sessions incomplètes au démarrage
- ✅ **WSL-compatible** - Détection automatique et utilisation de PollingObserver
- ✅ **Real-time watching** - Détecte et traite les nouvelles images en temps réel
- ✅ **Storage Pattern** - Abstraction filesystem (LocalStorage, S3-ready)

## Architecture

### Composants

```
sd-generator-watchdog/
├── observer_factory.py       # WSL detection + Observer selection
├── thumbnail_sync.py          # Service principal de génération
└── cli.py                     # CLI entry point (sdgen-watchdog thumbnail)
```

### Intégration avec WebUI

```
sdgen webui start
  ├── Session Watchdog      # Sync sessions → DB
  └── Thumbnail Watchdog    # PNG → WebP thumbnails
```

## Smart Catchup Algorithm

### Problème résolu

**Avant (naïf) :**
- Parcourait TOUTES les sessions à chaque démarrage
- O(N sessions × M images) → plusieurs minutes pour 1000+ sessions
- Gaspillait du temps sur des sessions déjà traitées

**Après (smart) :**
- O(1) dans le cas normal (nouveau run)
- O(K) où K = nombre de sessions incomplètes
- Démarrage ultra-rapide même avec 1M+ images

### Algorithme

**Stratégie :**
```
1. Trier sessions par date création (newest → oldest)
2. Pour chaque session :
   a. Compter thumbnails existants vs images sources
   b. Si counts match → session complète, skip
   c. Si mismatch → session incomplète, traiter
3. Continuer jusqu'à trouver une session complète
4. Stop (assume sessions plus anciennes sont complètes)
```

**Exemples :**

**Cas 1 : Nouveau run (optimal)**
```
Session_2025_11_10  [0/100 thumbs]  → Traiter ✓
Session_2025_11_09  [50/50 thumbs]  → Skip, STOP ✓
Session_2025_11_08  [30/30 thumbs]  → Non vérifié (stop avant)
...
```
Résultat : 1 session traitée, démarrage instantané

**Cas 2 : Redémarrage après crash**
```
Session_2025_11_10  [0/100 thumbs]  → Traiter ✓
Session_2025_11_09  [30/50 thumbs]  → Traiter ✓
Session_2025_11_08  [0/30 thumbs]   → Traiter ✓
Session_2025_11_07  [25/25 thumbs]  → Skip, STOP ✓
```
Résultat : 3 sessions incomplètes traitées, reprend où ça s'est arrêté

**Cas 3 : Déjà à jour**
```
Session_2025_11_10  [100/100 thumbs]  → Skip
Session_2025_11_09  [50/50 thumbs]    → Skip
...
```
Résultat : 0 sessions traitées, "✓ All sessions up-to-date"

### Implémentation

**Location :** `thumbnail_sync.py:162` - `initial_catchup()`

```python
async def initial_catchup(self) -> None:
    # Sort sessions newest → oldest
    sessions_sorted = sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)

    found_incomplete = False

    for session_path in sessions_sorted:
        source_count = count_images(session_path, [".png"])
        thumb_count = count_thumbnails(session_path)

        if source_count == thumb_count:
            # Complete session
            if found_incomplete:
                break  # Stop - older sessions assumed complete
            continue   # Skip this complete session

        # Incomplete - process it
        found_incomplete = True
        process_session(session_path)
```

## WSL Compatibility

### Problème : inotify sur WSL

**Symptôme :** Le watchdog démarre, fait le catchup, puis ne détecte AUCUNE nouvelle image.

**Cause :** Sur WSL, les montages NTFS (`/mnt/d`, `/mnt/c`) n'émettent PAS d'événements inotify.

**Solution :** Détection automatique WSL + fallback vers `PollingObserver`.

### Observer Factory Pattern

**Location :** `observer_factory.py`

```python
def is_wsl() -> bool:
    """Detect if running under WSL."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False

def get_observer_class() -> Any:
    """Get appropriate Observer class based on platform."""
    if is_wsl():
        logger.info("🐧 WSL detected - using PollingObserver")
        return PollingObserver  # Polling (fallback)
    return Observer  # inotify/kqueue (performant)
```

**Avantages :**
- ✅ Fonctionne sur WSL sans configuration
- ✅ Performant sur Linux/macOS natifs (inotify)
- ✅ DRY - Factory partagée entre `thumbnail_sync.py` et `session_sync.py`

### Polling vs inotify

| | inotify (Observer) | Polling (PollingObserver) |
|---|---|---|
| **Performance** | Instantané | ~1s latency |
| **CPU usage** | Minimal | Légèrement plus élevé |
| **WSL /mnt/** | ❌ Ne fonctionne pas | ✅ Fonctionne |
| **Linux natif** | ✅ Recommandé | ✅ Fallback |

## Storage Pattern

### Abstraction filesystem

Le watchdog utilise le **Storage Pattern** pour abstraction filesystem :

```python
# Interfaces (sd-generator-webui/storage/)
ImageStorage      # CRUD images (read_bytes, write_bytes, exists)
SessionStorage    # Operations sessions (list_sessions, count_images)

# Implémentations
LocalImageStorage     # pathlib (local filesystem)
LocalSessionStorage   # pathlib (local filesystem)

# Future: S3ImageStorage, S3SessionStorage
```

**Avantages :**
- ✅ Business logic découplée du filesystem
- ✅ Testable (mock storage)
- ✅ S3/MinIO-ready (future)

### Dépendances

Le watchdog **dépend** du package `sd-generator-webui` pour :
- `ImageStorage` / `SessionStorage` interfaces
- Pas de duplication de code filesystem

**Déclaration :** `pyproject.toml` (note, pas de dépendance explicite)
```toml
# Note: sd-generator-webui imported for Storage interfaces
# Installed via workspace dependency, not declared here
```

## Configuration

### Démarrage automatique

Le watchdog est lancé automatiquement par `sdgen webui start` :

**Location :** `daemon.py:480` - `start_thumbnail_watchdog()`

```python
def start_thumbnail_watchdog(
    sessions_dir: Path,
    target_dir: Optional[Path] = None
) -> Optional[int]:
    if target_dir is None:
        target_dir = Path.cwd() / "thumbnails"  # Relatif au CWD

    cmd = [
        sys.executable, "-m", "sd_generator_watchdog.cli", "thumbnail",
        "--source-dir", str(sessions_dir),
        "--target-dir", str(target_dir)
    ]

    proc = subprocess.Popen(cmd, ...)
    write_pid("thumbnail_watchdog", proc.pid)
```

### Chemins par défaut

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `--source-dir` | `./results` | Sessions à surveiller (PNG sources) |
| `--target-dir` | `./thumbnails` | Destination thumbnails (WebP) |

**Note :** Les chemins sont **relatifs au CWD** (là où `sdgen_config.json` est situé).

### Logs

```bash
# Logs du watchdog
tail -f ~/.sdgen/logs/thumbnail_watchdog.log

# PID file
cat ~/.sdgen/pids/thumbnail_watchdog.pid
```

## Performance

### Metrics (exemple réel)

**Environnement de test :**
- 1090 sessions
- 68 370 images PNG
- WSL 2 + NTFS mount

**Résultats smart catchup :**
```
🔄 Starting smart catch-up: /mnt/d/.../results
📂 Found 1090 sessions
📍 Processing incomplete session: 20251110_151059-test (0/374 thumbnails)
✓ Found complete session: 20251109_183422-old, stopping catch-up

✓ Initial catch-up complete:
  ✓ Processed: 374
  ⊘ Skipped: 0
  📦 Sessions processed: 1
  ✗ Errors: 0

⏱️ Duration: ~30s (374 thumbnails générés)
```

**Sans smart catchup :** Aurait parcouru les 1090 sessions → plusieurs minutes

**Gain :** ~90% de temps économisé au démarrage

### Génération thumbnails

**Specs :**
- Format : WebP (quality 85, method 6)
- Hauteur : 240px (aspect ratio preserved)
- Conversion RGB si nécessaire (P, RGBA, LA modes)

**Performance moyenne :** ~12 thumbnails/seconde (PIL + WebP encoding)

## Troubleshooting

### Le watchdog ne détecte pas les nouvelles images

**Symptômes :**
```
✓ Initial catch-up complete
👀 Watching for new images...
[Puis plus rien, même si on crée des PNG]
```

**Cause probable :** WSL + inotify ne fonctionne pas sur `/mnt/`

**Vérification :**
```bash
# Check si PollingObserver est activé
tail -f ~/.sdgen/logs/thumbnail_watchdog.log | grep "WSL detected"
# Devrait afficher : 🐧 WSL detected - using PollingObserver
```

**Fix :** Le code détecte automatiquement WSL depuis l'observer_factory. Si ça ne marche toujours pas, vérifier `/proc/version`.

### Catchup trop lent

**Si le catchup initial prend trop de temps :**

1. **Vérifier nombre de sessions incomplètes :**
   ```bash
   # Nombre de sessions traitées dans les logs
   grep "Sessions processed" ~/.sdgen/logs/thumbnail_watchdog.log
   ```

2. **Si toutes les sessions sont incomplètes** → Probable première exécution ou corruption du dossier `thumbnails/`

3. **Solution :** Laisser tourner une fois (génère tous les thumbnails), les prochains démarrages seront instantanés

### Thumbnails manquants

**Si des thumbnails ne sont pas générés :**

1. **Check errors dans les logs :**
   ```bash
   grep "✗" ~/.sdgen/logs/thumbnail_watchdog.log
   ```

2. **Vérifier permissions :**
   ```bash
   ls -la ./thumbnails/
   # Doit être writable
   ```

3. **Forcer un re-catchup :**
   ```bash
   # Supprimer thumbnails d'une session spécifique
   rm -rf ./thumbnails/20251110_151059-test/

   # Restart watchdog
   sdgen webui restart
   ```

## API on-demand fallback

Le watchdog travaille en **tandem** avec l'API :

**Stratégie dual-path :**
1. **Watchdog (eager)** - Génère en arrière-plan dès qu'une PNG est créée
2. **API (on-demand)** - Génère à la volée si thumbnail manquant (fallback)

**Location API :** `sd-generator-webui/backend/api/images.py:137`

```python
if thumbnail:
    thumbnail_path = THUMBNAILS_DIR / Path(filename).with_suffix(".webp")

    if not thumbnail_path.exists():
        # Watchdog hasn't generated it yet → generate on-demand
        generate_thumbnail_sync(source_path, thumbnail_path)
```

**Avantages :**
- ✅ Robuste - Fonctionne même si watchdog est down
- ✅ Pas de latence - Watchdog pré-génère
- ✅ Pas de gap - API génère si manquant

## Future Improvements

### Planned

- [ ] **Incremental catchup** - Checkpoint dernière session traitée (évite re-scan)
- [ ] **Parallel processing** - asyncio/multiprocessing pour génération batch
- [ ] **Configurable polling interval** - Ajuster latency vs CPU usage
- [ ] **Delete detection** - Supprimer thumbnails si source PNG supprimée

### Considéré mais rejeté

- ❌ **Force regeneration flag** - API on-demand suffit
- ❌ **Watch thumbnail dir** - Source of truth = source PNG, pas les thumbnails

## Références

- Code: `packages/sd-generator-watchdog/`
- Storage Pattern: `docs/backend/storage-pattern.md` (à créer)
- Observer Pattern: https://python-watchdog.readthedocs.io/
- WSL inotify issue: https://github.com/microsoft/WSL/issues/4739
