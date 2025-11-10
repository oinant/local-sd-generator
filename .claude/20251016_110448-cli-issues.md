# CLI ISSUES : 

##  sdgen --help => OK


```bash 
╭─      /mnt/d/StableDiffusion/private-new  on    main ⇡1 !1 ?3 ······································································································· ✔  at 10:45:13   ─╮
╰─ sdgen --help                                                                                                                                                                                    ─╯

 Usage: sdgen [OPTIONS] COMMAND [ARGS]...

 SD Image Generator - YAML Template Mode (Phase 2)

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                        │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ start      Start the complete SD Generator environment.                                                                                                                                            │
│ stop       Stop all SD Generator services.                                                                                                                                                         │
│ status     Show status of all SD Generator services.                                                                                                                                               │
│ generate   Generate images from YAML template using V2.0 Template System.                                                                                                                          │
│ list       List available YAML templates with rich formatting.                                                                                                                                     │
│ init       Initialize global configuration file interactively.                                                                                                                                     │
│ validate   Validate a YAML template file using V2.0 Template System.                                                                                                                               │
│ api        API introspection commands (list models, samplers, etc.)                                                                                                                                │
│ webui      Manage WebUI services (backend + frontend)                                                                                                                                              │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## sdgen start  => KO

```bash 
╭─      /mnt/d/StableDiffusion/private-new  on    main ⇡1 !1 ?3 ······································································································· ✔  at 10:45:47   ─╮
╰─ sdgen start                                                                                                                                                                                     ─╯
╭─────────────────────────────────────╮
│ SD Generator - Starting Environment │
╰─────────────────────────────────────╯
✗ Error: 'GlobalConfig' object has no attribute 'get'
```

## sdgen start --help  => OK

```bash 
╭─      /mnt/d/StableDiffusion/private-new  on    main ⇡1 !1 ?3 ····································································································· 1 ✘  at 10:45:57   ─╮
╰─ sdgen start --help                                                                                                                                                                              ─╯

 Usage: sdgen start [OPTIONS]

 Start the complete SD Generator environment.

 Launches services in background (non-blocking): - Automatic1111 WebUI (optional, --start-a1111) - Backend FastAPI server - Frontend Vite dev server (unless --no-frontend)
 Examples:     sdgen start     sdgen start --start-a1111     sdgen start --start-a1111 --a1111-bat /mnt/d/sd/webui.bat     sdgen start --no-frontend --backend-port 8080

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --start-a1111                      Start Automatic1111 on Windows (WSL only)                                                                                                                       │
│ --a1111-bat               TEXT     Path to Automatic1111 webui.bat                                                                                                                                 │
│ --backend-port   -bp      INTEGER  Backend server port [default: 8000]                                                                                                                             │
│ --frontend-port  -fp      INTEGER  Frontend dev server port [default: 5173]                                                                                                                        │
│ --no-frontend                      Don\'t start frontend                                                                                                                                            │
│ --no-reload                        Disable backend auto-reload                                                                                                                                     │
│ --dev-mode                         Start in dev mode (separate frontend server)                                                                                                                    │
│ --help                             Show this message and exit.                                                                                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
