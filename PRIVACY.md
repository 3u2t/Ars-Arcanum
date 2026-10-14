# Privacy & Data Sovereignty Statement (`PRIVACY.md`)

**Ars Arcanum collects zero telemetry, makes zero network calls during authoring workflows, and stores 100% of data locally on your filesystem.**

- **No Cloud Sync or Third-Party Servers**: Your universes (`~/Universes/`), manuscripts (`~/Manuscripts/`), caches (`.arcanum_cache.json`), and writing sprint logs (`.arcanum/sprint_log.jsonl`) never leave your machine.
- **No Generative AI Training or Scraping**: Ars Arcanum is a deterministic continuity compiler and manuscript engineering suite. Your prose is never sent to external APIs or language models.
- **CI Verification of Offline Invariants**: Every commit on `main` is scanned by `.github/workflows/ci.yml` to verify that zero remote CDN links (`https://cdn...`, `unpkg`, `cdnjs`) exist anywhere in `scripts/lib/` or `src/arcanum/`.
