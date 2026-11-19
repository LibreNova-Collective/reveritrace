# Release notes
## ReveriTrace 1.0.0 (candidate)
- Independent YouTube and YouTube Music history finder; no publisher account association, no private bindings or credentials.
- ZIP/JSON history import, incremental batches, ISO date filtering, duplicate detection, repeated activity grouping.
- Local LSA, multilingual title expansion in English, Spanish and Japanese; optional offline neural engine (real model not verified).
- Safe read-only copy comparison; no automatic deletions. Google account setup remains user-controlled.
- Public listing draft, icon, review prompts, Spanish translation, privacy/terms/support drafts, technical and user documentation.
- Eighteen synthetic tests passed; no direct OAuth/live Google import, portal validation or publication performed.

## Private Digital History Finder 0.5.0
- Replace per-session full export request with hybrid schedule (every 2 months for one year) plus incremental import at first invocation when available.
- Reuse pending/active provider plan. Report authentication blocker. Maintain safe rotation and cumulative index; no actual deletion without validated replacement.

## Licensing update (unpublished candidate)
- Original code licensed AGPL-3.0-only; full license text, SPDX headers and bilingual community contribution guidance included.

### v1.0.1
36 synthetic tests passed. External model manifest gate and safe loading flags tested without actual weights. No bundled model weights, credentials or third-party binary dependencies. Public publisher, live URLs, portal scans and attestations remain pending.

## Preparación de publicación de 1.0.1

Se conserva la versión declarada. La distribución usa un inventario explícito, archivos ZIP con metadatos fijos y validación estricta de aprobaciones. Se incorporan pruebas de exclusión de archivos ajenos, enlaces simbólicos, salidas contaminadas y estructura del plugin. CI y Pages se preparan para el repositorio público, con ejecución privada local durante la revisión.
