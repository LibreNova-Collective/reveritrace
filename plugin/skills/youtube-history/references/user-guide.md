# ReveriTrace 1.0.0 — User guide / Manual de usuario

## Purpose / Propósito
ReveriTrace helps someone rediscover their own previously watched videos and listened-to tracks from YouTube and YouTube Music. It indexes their authorized history exports; it does not reconstruct deleted records, play media, automatically log in to Google, or provide live access to all account activity.

ReveriTrace permite reencontrar vídeos y canciones mediante archivos propios de historial. No requiere una cuenta del creador. No recupera datos eliminados ni incluye un conector OAuth propio.

## English quick start
1. Sign in to your own Google account at https://takeout.google.com/. Deselect everything except YouTube and YouTube Music; select history only and JSON format. Choose ZIP and an approved destination. Download when Google notifies you.
2. Provide the account's history archive in a supported ChatGPT session, or use a user-approved local folder. For a connected Drive, grant access to your own account through the host connector and identify your exact export folder; connector availability and binary file access vary.
3. Ask: “Find a video I watched around June 2024, with a Japanese title and English subtitles.” Results include the recorded timestamps, title and link when available; metadata search may suggest a candidate but cannot verify subtitles from text alone.
4. For refreshing, optionally configure Google's recurring export once every two months for one year. A local synchronized folder can automatically import newly arrived exports. No full export is triggered when a skill launches.
5. If you switch Google accounts, use a new index and folder. Never share passwords, codes, cookie files or unrelated Takeout data.

## Inicio rápido en español
1. En https://takeout.google.com/, inicia sesión en tu cuenta y selecciona únicamente YouTube y YouTube Music, categoría historial y formato JSON. Genera ZIP y elige un destino autorizado.
2. Adjunta el ZIP en una sesión compatible, o selecciona una carpeta propia sincronizada. Si el servicio permite una conexión a Drive, autoriza tu cuenta mediante el proveedor, no mediante el chat.
3. Prueba «Encuentra el vídeo musical japonés que vi en junio», «¿Qué pistas escuché varios días?» o «Filtra por canciones instrumentales».
4. Opcional: programa desde Google exportaciones cada dos meses durante un año. Se revisa la carpeta al iniciar una sesión compatible, no se crea una exportación nueva por sesión.
5. Usa una base de datos distinta por cuenta. Para eliminar copias locales, cierra los procesos y elimina la base de datos y sus archivos auxiliares siguiendo las instrucciones de tu sistema; no afecta el historial de Google. Si cambias de cuenta, revoca el acceso de la conexión anterior según el proveedor.

## Standalone local CLI
Use Python 3.9+ (a current supported Python is recommended). Run from the package's `skills/youtube-history/scripts` folder. Install optional lexical/LSA dependencies locally: `python -m pip install numpy scikit-learn`. On systems without timezone definitions, install `tzdata` or use UTC. Optional sentence-transformers weights must be independently installed and downloaded in advance; neural mode is not verified with actual weights in the release.

```
python history.py --db /private/account-a/history.sqlite configure --inbox /private/account-a/takeout
python history.py --db /private/account-a/history.sqlite start
python history.py --db /private/account-a/history.sqlite stats
python history.py --db /private/account-a/history.sqlite search --from 2024-06-01 --to 2024-06-30 --tz UTC --query 'ambient music|instrumental' --expand
python history.py --db /private/account-a/history.sqlite sync /private/account-a/takeout --watch --interval 300
```
On Windows use quoted real paths or `py -3`. Create the DB parent folder first. The last command polls only while running; installation schedules no background process. A compatible OS scheduler is optional and user-configured.

## Coverage and privacy
Counts mean events recorded, not total listening time. A link normalized to youtube.com may not distinguish the original Music surface. Searches and plays are separate. History is stored in SQLite outside the package. Device access controls matter; SQLite bundles no encryption at rest. A cloud ChatGPT session or connector is not the same as offline device processing. Use the host privacy controls; do not assume files survive chats or are deleted automatically when a local file is removed. No publisher backend is included.

## External model safety and licensing (v1.0.1)
Use only separately obtained local model artifacts permitted by `model_policy.py` and documented in `references/model-policy.md` (from SKILL.md) or `model-policy.md` (from this reference directory). The manifest records a reviewed license, source revision and SHA-256 checksums. Unknown or unreviewed models fall back to LSA/lexical. No model API or model weights are bundled. Do not send history to a remote embedding service. Neural inference has not been verified with real weights.
