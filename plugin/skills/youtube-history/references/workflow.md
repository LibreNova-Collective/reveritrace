# User workflows
1. On Google Takeout choose only YouTube and YouTube Music, history, JSON, ZIP. Download or select an authorized destination. An optional recurring export every two months for one year is a Google feature, not a live feed. Google may require further verification.
2. Import supplied files into a separate private database per account, preferably via a dedicated local directory synced by the user's own approved software. `configure --inbox` saves the folder; `start`, `stats`, and `search` recheck it. Actual data access depends on the host.
3. Query date ranges and approximate titles, channels, moods or subtitle labels. Optional public metadata verification is separate from personal evidence. Local semantic mode uses LSA; optional offline neural mode requires independently installed weights, not included or tested end-to-end.
4. Apply incremental batches only from user-provided or authorized sources, with exact timestamps. See hybrid.md. No automated remote access, credential management or scheduled cloud service is bundled.
5. Verify archives before any user-directed cleanup, see rotation.md. `verify_rotation.py` never deletes.
