# Technical Specification (MVP): Documentation Sync and Consolidation System for Standard NotebookLM RAG

**Version:** 1.0-MVP
**Scope:** Static, server-rendered HTML documentation sites
**Reference target:** [Bolivia SIAT — Sistema de Facturación](https://siatinfo.impuestos.gob.bo/index.php/sistema-facturacion) and similar government/CMS-rendered technical documentation portals.

---

## 1. Purpose and MVP Scope

This system automates the extraction, normalization, consolidation, and maintenance of **static, server-rendered** technical web documentation into a small number of high-volume Markdown files, designed specifically for **manual ingestion into standard NotebookLM**.

### Concrete reference use case

The first real-world target is the Bolivian tax authority's invoicing system documentation (SIAT), a Joomla-rendered site containing:

- General information about billing modalities (electronic, manual, computerized)
- System authorization procedures
- Technical annexes and sector-specific document definitions
- Synchronization and catalog specifications
- Regulatory resolutions (RNDs) and their technical annexes

The same system must work for any documentation that shares these characteristics: **server-rendered HTML, hierarchical URL structure, stable content, no heavy JavaScript dependency**.

### What the MVP solves

NotebookLM Standard allows up to **50 sources per notebook** (free tier) and treats each uploaded source as a **static copy** (confirmed against Google's current documentation). Keeping a corpus like SIAT — dozens of pages, periodically updated, spread across many URLs — synchronized inside NotebookLM is costly without tooling.

The MVP solves this with:

- Deterministic extraction from a curated list of URLs.
- Incremental change detection based on normalized content.
- Consolidation of many URLs into a minimal number of Markdown containers that fit within NotebookLM's source limits.
- State persistence to avoid redundant reprocessing.
- A clear operator manifest describing exactly what must be re-uploaded after each run.

### What the MVP does **not** do (deferred to v2)

To keep the MVP shippable, the following are explicitly out of scope:

- Headless browser rendering (Playwright/Chromium).
- JavaScript-rendered SPAs (Docusaurus, VitePress, Nextra, etc.).
- Framework-specific extraction profiles.
- Browser extension for manual recipe authoring.
- Automatic sync with NotebookLM (no such public API exists).
- Massive domain crawling without a curated URL list.
- Multi-objective optimal rebalancing (we use a simple deterministic greedy).
- Image/diagram downloading (we preserve references as links only).

Items removed from the original specification are tracked in Section 16 (Roadmap) so nothing is lost.

---

## 2. Target Documentation Profile

The MVP is designed for documentation that satisfies **all** of the following:

| Characteristic | Required for MVP |
|---|---|
| Server-rendered HTML (content present in the initial HTTP response) | Yes |
| Stable URL structure (URLs don't rotate between runs) | Yes |
| Content accessible without authentication | Yes |
| `robots.txt` allows crawling the documentation paths | Yes |
| Page sizes reasonable (individual pages under ~50k words) | Yes |
| JavaScript required for main content | **No** (if yes → defer to v2) |

**SIAT compliance check:**

- Server-rendered Joomla HTML → ✅
- Stable `/index.php/…` paths → ✅
- Public documentation → ✅
- No authentication required → ✅
- Pages small (typically under 5k words each) → ✅
- No SPA hydration → ✅

The SIAT site is a good fit. Any similar CMS (Joomla, Drupal, WordPress, MediaWiki, plain static HTML, Jekyll/Hugo output) will work the same way.

### Known quirks the MVP must tolerate

- **Loose SSL configuration.** Many `.gob.bo` sites have certificate chains that fail strict validation. The fetcher must support a configurable flag to relax certificate verification **per domain** (not globally), and log when it does.
- **JavaScript-obfuscated content fragments.** Joomla protects email addresses with `<script>` blocks. These are irrelevant to documentation content and can be safely stripped.
- **Duplicated navigation blocks.** CMS layouts repeat sidebars, breadcrumbs, and footers. These must be removed before hashing.

---

## 3. Design Principles

1. **Logical-content determinism.** The same URL, processed with the same extractor version against the same source HTML, must produce the same **logical content hash**. The ensembled Markdown block may differ byte-by-byte between runs (because of the extraction timestamp in the header); that is acceptable as long as the content hash is stable.
2. **State persistence.** No URL is reprocessed or redistributed unnecessarily.
3. **Controlled degradation.** If one extraction path fails, the system falls back to the next without losing traceability. URLs that cannot be extracted confidently go to a manual review queue; the last known good content is retained.
4. **Separation of extraction and packaging.** Each URL is managed as an independent unit before consolidation.
5. **Conservative NotebookLM compatibility.** All containers stay well below a conservative operational threshold to absorb word-counting ambiguity (see Section 5.3).
6. **Safe-by-default scraping.** The system honors `robots.txt`, applies per-domain rate limits, and identifies itself with a contact-carrying User-Agent.

---

## 4. Pipeline Architecture

The MVP pipeline is linear, not a complex cascade. There are three extraction levels instead of five.

```
Level 0: Normalization + Precheck
    │
    ▼
Level 1: HTTP Fetch (conditional GET)
    │
    ▼
Level 2: Semantic Extraction (readability)
    │
    ▼
        ┌─ confidence OK  → Canonical Markdown Unit
        │
        └─ low confidence → NEEDS_REVIEW queue (keep last good content)
```

### Level 0: Normalization and Precheck

Before any content is fetched, for each URL the system must:

- Normalize the URL (trim fragments, lowercase host, decode percent-encoding where safe, sort deterministic query parameters).
- Resolve redirects on a first fetch and persist the final URL.
- Extract `<link rel="canonical">` when present; if canonical differs from the normalized URL, record the mapping but do **not** automatically follow it for the MVP — the operator decides whether to replace the entry.
- Verify `Content-Type` is HTML; reject other types as `UNSUPPORTED`.
- Record HTTP status, estimated length, and response headers needed for conditional GET (`ETag`, `Last-Modified`).
- Consult `robots.txt` for the domain; if the URL is disallowed, mark it `BLOCKED_BY_ROBOTS` and skip.

If the URL cannot pass precheck, it is recorded as `UNSUPPORTED`, `FAILED_PRECHECK`, or `BLOCKED_BY_ROBOTS` and excluded from further processing.

### Level 1: HTTP Fetch

Fetching uses conditional `GET` with `If-None-Match` and `If-Modified-Since` when prior validators exist.

- **304 Not Modified** → skip reprocessing; update last-seen timestamp only.
- **200 OK** → pass the response body to Level 2.
- **4xx/5xx** → record the error and apply the retry policy (Section 9).

`HEAD` is **not** used in the MVP. Many CMS and CDN configurations return inconsistent metadata on `HEAD`. `GET` with conditional headers is both simpler and more reliable.

### Level 2: Semantic Extraction

Given the HTML body, the system applies a readability extractor (`trafilatura` is the MVP choice; `readability-lxml` is a backup).

The extractor must:

- Strip navigation, sidebars, breadcrumbs, footers, and scripts using `selectolax`.
- Preserve heading hierarchy, ordered/unordered lists, code blocks, and tables using `markdownify` in GFM mode.
- Post-process the Markdown using regular expressions to:
    - **Eradicate Images**: Remove all `![alt](url)` patterns.
    - **Flatten Links**: Replace `[text](url)` with `text` to save tokens.
- Emit a **confidence score** in the range `[0.0, 1.0]`.

A domain-specific **selector hint** (CSS selector, optional) can be stored per domain to help the extractor when readability alone underperforms. This is a simpler version of the original spec's "recipes" and is restricted to:

- A single `include` CSS selector for the main content container.
- A list of `exclude` CSS selectors for subtrees to strip.

No JavaScript actions, no XPath, no headless steps. If a site genuinely requires more than this, it does not qualify for the MVP and is deferred to v2.

#### Confidence and review thresholds

Let `C` be the extraction confidence reported by the extractor, and let `W` be the word count of the extracted content.

- `C >= 0.70` and `W >= 100` → accept.
- `C < 0.70` **or** `W < 100` → mark the URL as `NEEDS_REVIEW`, **retain the last known good content** in the container, and add an entry to the review queue with the suspected cause.
- `C < 0.70` **and** `W < 30` → treat as a probable extraction failure; raise a warning and do not overwrite prior content.

These numeric thresholds are configurable per project.

---

## 5. Content Normalization and Canonical Format

Each URL is converted into a **canonical documentation unit** before being placed in a container.

### 5.1 Mandatory header per unit

Each Markdown block generated from a URL begins with a structured YAML-like header:

```md
<!-- unit:begin id={unit_id} -->
# {normalized_title}

- Source URL: {final_url}
- Project: {project_id}
- Extracted at: {timestamp_utc_iso8601}
- Extractor version: {extractor_version}
- Content hash: {content_hash_sha256}
<!-- unit:header-end -->

{body_markdown}

<!-- unit:end id={unit_id} -->
```

The HTML-style comment markers are **stable anchors**: they are used by the assembler, by diff tooling, and by the manifest generator to locate units inside a container without parsing Markdown structure. NotebookLM ignores HTML comments.

### 5.2 Definition of the content hash (fix for the circular-hash problem)

The `content_hash_sha256` is computed as follows:

1. Take the `{body_markdown}` **only** — everything between `<!-- unit:header-end -->` and `<!-- unit:end -->` — not including the header.
2. Normalize it:
   - Convert line endings to `\n`.
   - Strip trailing whitespace on each line.
   - Collapse runs of 3+ blank lines into 2.
   - Do **not** modify code-block contents.
3. SHA-256 the UTF-8 bytes of the normalized body.

This makes the hash independent of the extraction timestamp and of the header, which solves the circular-hash problem in the original specification. The hash is stable across runs when the underlying content is unchanged, regardless of when it was extracted.

A second hash, `assembly_hash_sha256`, covers the full assembled container file and is used to decide whether the operator needs to re-upload that container.

### 5.3 Word counting policy (fix for the word-count ambiguity)

NotebookLM's internal word counting is **not** a simple whitespace split. Google's own documentation notes that structural characters (table borders, cell boundaries, etc.) are included in their count, and an apparent word count below 500,000 can still exceed the limit.

To defend against this:

#### Counting method

The system computes two metrics per unit:

- `word_count`: whitespace-split tokens of the body Markdown **plus** an inflation factor for Markdown syntax:
  - Each table row contributes `max(whitespace_words, cell_count * 2)`.
  - Each code block contributes `max(whitespace_words, non_whitespace_tokens * 1.2)`.
  - Each header line contributes `words + 1`.
- `char_count`: raw UTF-8 character count of the body.

#### Conservative container thresholds

The thresholds are intentionally lower than the original specification to absorb the counting discrepancy:

| State | Word count | Character count (safety) |
|---|---|---|
| `ACTIVE` (accepts new URLs) | up to 250,000 | up to 1,500,000 |
| `WARM` (no new URLs, tolerates growth) | 250,001 – 320,000 | up to 1,900,000 |
| `NEAR_LIMIT` (updates only) | 320,001 – 380,000 | up to 2,300,000 |
| `SPLIT_PENDING` (must rebalance) | 380,001 – 430,000 | up to 2,600,000 |
| `CRITICAL` (final assembly blocked) | > 430,000 | > 2,600,000 |

The NotebookLM hard limit is 500,000 words / ~200MB per source. The MVP leaves **~70,000 words of headroom** between `SPLIT_PENDING` and the external limit, giving ample room for Google's stricter counting.

#### Empirical calibration (required before first production run)

Before the first production run, the operator must:

1. Upload three sample containers of different sizes (e.g., 150k, 250k, 350k computed words) to NotebookLM.
2. Record the word count that NotebookLM reports for each.
3. If NotebookLM's reported count exceeds our count by more than 15%, adjust the `word_count_inflation_factor` project setting upward and rerun the calibration.

The thresholds above assume the calibrated factor is ≤ 1.15. Record the measurements in the `projects.calibration_notes` column.

### 5.4 Normalization rules

- Normalize line endings.
- Remove repeated non-documentation blocks (nav, cookie banners, repeated footers).
- Preserve headings and code blocks.
- Convert tables to Markdown only when every row is well-formed; otherwise degrade to a plain-text representation with separators preserved.
- Deduplicate identical consecutive blocks inside the same page (common in CMS-generated TOCs).
- Reject empty sections and invalid heading hierarchies (`H1 → H3` without `H2` gets flattened).
- Preserve image references as Markdown links (`![alt](url)`) with absolute URLs. The MVP does **not** download images; v2 will add this.

---

## 6. Synchronization and Change Detection

The goal is to minimize bandwidth, CPU, and container rewrites.

### 6.1 Change detection strategy

For each URL on each run:

1. Issue a conditional `GET` using stored `ETag`/`Last-Modified`.
2. If `304`, mark the unit `UNCHANGED` and proceed.
3. If `200`, extract and normalize. Compute the new `content_hash_sha256`.
4. Compare against the stored hash:
   - Identical → mark `UNCHANGED`, update only network metadata (new `ETag`, etc.).
   - Different → mark `CHANGED`, stage the new unit for container update.

The content hash is the **source of truth**. Network headers are an optimization only.

### 6.2 Conservative deletion policy

A URL is **not** deleted the first time it fails. Specifically:

- A URL is marked `DELETED` only after **3 consecutive failed runs** over a span of **at least 14 days**, all returning `404` or `410`.
- While in the failing state, the last-known-good content remains in the container, annotated with `<!-- unit:stale since={date} reason={code} -->` inside the header comments.
- A single transient failure (5xx, timeout, DNS error) never triggers deletion; it increments `consecutive_failures` and retries on the next run.

### 6.3 Error taxonomy (replaces free-text `ultimo_error_codigo`)

| Code | Category | Retry policy |
|---|---|---|
| `HTTP_4XX_CLIENT` | permanent unless proven otherwise | retry once next run; after 3 consecutive → `DELETED` per 6.2 |
| `HTTP_5XX_SERVER` | transient | exponential backoff within run, retry next run |
| `HTTP_429_RATE_LIMIT` | transient | respect `Retry-After`, exponential backoff |
| `NETWORK_TIMEOUT` | transient | retry with longer timeout next run |
| `NETWORK_DNS` | transient | retry next run |
| `SSL_VERIFY_FAIL` | configuration | surface to operator; do not retry silently |
| `ROBOTS_DISALLOWED` | permanent | no retry |
| `CONTENT_TYPE_UNSUPPORTED` | permanent | no retry |
| `EXTRACTION_LOW_CONFIDENCE` | review | `NEEDS_REVIEW`, keep prior content |
| `EXTRACTION_EMPTY` | review | `NEEDS_REVIEW`, keep prior content |
| `PARSE_ERROR` | transient | retry once; then `NEEDS_REVIEW` |

### 6.4 Rate limiting and politeness

- Per-domain rate limit: **1 request per second** by default, configurable per project.
- `robots.txt` is fetched once per run per domain and respected.
- `User-Agent` is configurable and must include a contact URL or email, e.g.: `NotebookLM-Doc-Sync/1.0 (+https://example.org/contact)`.
- Respect `Retry-After` on `429` and `503`.
- Concurrency across domains: up to N workers (default 4), but never more than 1 concurrent request to the same host.

### 6.5 Canonical URL deduplication

If two URLs in the project resolve to the same canonical URL:

- On the first run, the system logs a `CANONICAL_DUPLICATE` event and keeps both.
- The operator is prompted via the manifest to decide which URL to keep.
- Automatic deduplication is **not** performed in the MVP to avoid surprising the operator.

---

## 7. Container Consolidation (Bucketing)

The system packs multiple documentation units into consolidated Markdown files for manual upload to NotebookLM.

### 7.1 Objectives

- Minimize the number of files the operator must upload.
- Prefer **topical grouping** over pure volumetric packing, because RAG quality benefits from coherent containers (see the design note below).
- Keep assignments stable across runs (sticky assignment).

### 7.2 Design note on topical vs volumetric bucketing

Stuffing unrelated URLs into a single large file to maximize container fill hurts RAG retrieval: NotebookLM cites sources by filename, so a container called `siat_vol_01.md` containing 200 mixed topics yields worse citations than several topical containers.

The MVP **defaults to topical grouping with a volumetric cap**, not volumetric optimization. Each container is defined by a **topic path prefix** plus an ordinal:

- `siat_sistema_facturacion_vol_01.md`
- `siat_facturacion_manual_vol_01.md`
- `siat_normativa_rnd_vol_01.md`

URLs are assigned to containers by matching their canonical path against project-defined topic rules. Within a topic, the `vol_NN` suffix increments only when the previous volume reaches the ACTIVE→WARM threshold.

Topic rules are declared per project in a simple YAML file (see Section 10).

### 7.3 Stable assignment rule

Once a URL is assigned to a container, it stays there unless a rebalance forces a move. New URLs are assigned to the newest `ACTIVE` volume of their matching topic.

### 7.4 Deterministic internal ordering

Within a container, units are ordered by:

1. Section priority (optional integer, default 100).
2. Canonical path (alphabetical).
3. Canonical URL (alphabetical, tie-breaker).

This keeps diffs between versions minimal.

---

## 8. Overflow and Rebalancing (Simplified)

### 8.1 Container states

- `ACTIVE` — accepts new URLs.
- `WARM` — keeps existing URLs, accepts growth, no new assignments.
- `NEAR_LIMIT` — existing URL updates only.
- `SPLIT_PENDING` — next assembly must rebalance.
- `SEALED` — no further changes expected; manual operator decision.
- `ARCHIVED` — retained for history only.

Transitions are driven by the word-count thresholds in Section 5.3.

### 8.2 MVP rebalance algorithm (deterministic greedy)

When a container enters `SPLIT_PENDING`:

1. Load all units in the container, sorted by `(residency_time_descending, word_count_ascending)`. Older and smaller units are preferred to stay.
2. Target: bring the container to the middle of `ACTIVE` range (about 200k words).
3. Starting from the **end of the list** (newest, largest), pop units one at a time and move them to either:
   - An existing `ACTIVE` container of the same topic with enough room, or
   - A new `vol_NN+1` container of the same topic.
4. Stop when the source container is ≤ 250,000 words.

This is deliberately **simple and deterministic**. It is not optimal, but it is predictable, bounded in time, and easy to reason about. v2 can introduce a smarter algorithm if needed.

### 8.3 Oversized-unit policy

If a single unit exceeds **80,000 words** (configurable), it is marked `OVERSIZED_UNIT` and placed in a dedicated single-unit container. The MVP does **not** split a single URL's content across containers.

---

## 9. Data Model (SQLite)

SQLite runs in **WAL mode** for reader-writer concurrency. All writes go through a single writer worker; multiple readers are supported.

### 9.1 Schema migrations

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);
```

Every schema change bumps the version. The application refuses to start if the live DB version does not match the expected one, unless it can run the pending migrations.

### 9.2 Projects

```sql
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    primary_domain TEXT,
    user_agent TEXT NOT NULL,
    contact_url TEXT NOT NULL,
    rate_limit_per_host_rps REAL NOT NULL DEFAULT 1.0,
    word_count_inflation_factor REAL NOT NULL DEFAULT 1.15,
    container_target_words INTEGER NOT NULL DEFAULT 200000,
    container_warm_words INTEGER NOT NULL DEFAULT 250000,
    container_near_limit_words INTEGER NOT NULL DEFAULT 320000,
    container_split_pending_words INTEGER NOT NULL DEFAULT 380000,
    container_critical_words INTEGER NOT NULL DEFAULT 430000,
    oversized_unit_words INTEGER NOT NULL DEFAULT 80000,
    enabled INTEGER NOT NULL DEFAULT 1,
    calibration_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 9.3 Topic rules

```sql
CREATE TABLE topic_rules (
    rule_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    rule_order INTEGER NOT NULL,
    path_prefix TEXT NOT NULL,  -- e.g. '/index.php/facturacion-en-linea'
    topic_slug TEXT NOT NULL,   -- e.g. 'facturacion_en_linea'
    section_priority INTEGER NOT NULL DEFAULT 100,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX idx_topic_rules_project_order ON topic_rules(project_id, rule_order);
```

Rules are evaluated in `rule_order`; the first matching `path_prefix` wins.

### 9.4 Containers

```sql
CREATE TABLE containers (
    container_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    topic_slug TEXT NOT NULL,
    volume_number INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN (
        'ACTIVE','WARM','NEAR_LIMIT','SPLIT_PENDING','SEALED','ARCHIVED'
    )),
    current_words INTEGER NOT NULL DEFAULT 0,
    current_chars INTEGER NOT NULL DEFAULT 0,
    assigned_units INTEGER NOT NULL DEFAULT 0,
    assembly_hash_sha256 TEXT,
    assembly_version INTEGER NOT NULL DEFAULT 0,
    last_assembled_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, file_name),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX idx_containers_project_state ON containers(project_id, state);
CREATE INDEX idx_containers_topic ON containers(project_id, topic_slug, volume_number);
```

### 9.5 URL sources

```sql
CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    container_id TEXT,
    url_original TEXT NOT NULL,
    url_normalized TEXT NOT NULL,
    url_final TEXT,
    canonical_url TEXT,
    topic_slug TEXT,
    extracted_title TEXT,
    state TEXT NOT NULL CHECK(state IN (
        'ACTIVE','CHANGED','UNCHANGED','FAILED','NEEDS_REVIEW',
        'DELETED','UNSUPPORTED','BLOCKED_BY_ROBOTS','OVERSIZED_UNIT'
    )),
    extraction_level TEXT NOT NULL CHECK(extraction_level IN (
        'READABILITY','SELECTOR_HINT'
    )),
    extraction_confidence REAL,
    include_selector TEXT,
    exclude_selectors TEXT,
    http_status INTEGER,
    http_etag TEXT,
    http_last_modified TEXT,
    http_content_type TEXT,
    http_content_length INTEGER,
    content_hash_sha256 TEXT,
    unit_markdown_path TEXT,
    word_count INTEGER NOT NULL DEFAULT 0,
    char_count INTEGER NOT NULL DEFAULT 0,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    last_error_code TEXT,
    last_error_detail TEXT,
    last_success_at DATETIME,
    last_review_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (container_id) REFERENCES containers(container_id)
);

CREATE INDEX idx_sources_project_container ON sources(project_id, container_id);
CREATE INDEX idx_sources_state ON sources(state);
CREATE INDEX idx_sources_canonical ON sources(canonical_url);
```

### 9.6 Runs

```sql
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    project_id TEXT,
    run_type TEXT NOT NULL CHECK(run_type IN (
        'FULL','INCREMENTAL','REBALANCE_ONLY','RETRY_FAILED','DRY_RUN'
    )),
    state TEXT NOT NULL CHECK(state IN (
        'RUNNING','SUCCESS','PARTIAL_SUCCESS','FAILED'
    )),
    urls_evaluated INTEGER NOT NULL DEFAULT 0,
    urls_unchanged INTEGER NOT NULL DEFAULT 0,
    urls_changed INTEGER NOT NULL DEFAULT 0,
    urls_failed INTEGER NOT NULL DEFAULT 0,
    urls_review INTEGER NOT NULL DEFAULT 0,
    containers_rewritten INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    summary TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

### 9.7 Source events

```sql
CREATE TABLE source_events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT,
    source_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('INFO','WARN','ERROR')),
    event_type TEXT NOT NULL CHECK(event_type IN (
        'FETCH','EXTRACTION','HASH_COMPARE','REBALANCE','MANUAL_REVIEW',
        'CANONICAL_DUPLICATE','ROBOTS_CHECK','SSL_WARNING'
    )),
    message TEXT NOT NULL,
    detail_json TEXT,
    occurred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE INDEX idx_source_events_source_time ON source_events(source_id, occurred_at);
```

### 9.8 Review queue

```sql
CREATE TABLE review_queue (
    review_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'NORMAL' CHECK(priority IN (
        'LOW','NORMAL','HIGH','CRITICAL'
    )),
    state TEXT NOT NULL DEFAULT 'OPEN' CHECK(state IN (
        'OPEN','IN_PROGRESS','RESOLVED','WONT_FIX'
    )),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);
```

---

## 10. Project Configuration File

A project is declared in a YAML file loaded at start-up and synced into the `projects` and `topic_rules` tables.

```yaml
project_id: siat
name: Bolivia SIAT – Documentación del Sistema de Facturación
primary_domain: siatinfo.impuestos.gob.bo
user_agent: "NotebookLM-Doc-Sync/1.0 (+https://example.org/contact)"
contact_url: "https://example.org/contact"

fetch:
  rate_limit_per_host_rps: 1.0
  ssl_verify: false        # SIAT has cert chain issues; override explicit per project
  request_timeout_seconds: 30
  max_retries: 3

extraction:
  default_extractor: trafilatura
  min_confidence: 0.70
  min_words: 100

word_count:
  inflation_factor: 1.15
  container_thresholds:
    active_max: 250000
    warm_max: 320000
    near_limit_max: 380000
    split_pending_max: 430000

bucketing:
  topic_rules:
    - path_prefix: /index.php/sistema-facturacion
      topic_slug: sistema_facturacion
      section_priority: 10
    - path_prefix: /index.php/facturacion-en-linea
      topic_slug: facturacion_en_linea
      section_priority: 20
    - path_prefix: /index.php/facturacion-manual
      topic_slug: facturacion_manual
      section_priority: 30
    - path_prefix: /index.php/informacion
      topic_slug: informacion_general
      section_priority: 40
    - path_prefix: /
      topic_slug: otros
      section_priority: 999

seed_urls:
  - https://siatinfo.impuestos.gob.bo/index.php/sistema-facturacion
  - https://siatinfo.impuestos.gob.bo/index.php/facturacion-en-linea/factura-electronica
  - https://siatinfo.impuestos.gob.bo/index.php/facturacion-manual/solicitud-autorizacion
  # ...

selector_hints:
  - host: siatinfo.impuestos.gob.bo
    include: "div.item-page"      # Joomla main content container
    exclude:
      - "div.breadcrumbs"
      - "nav.navigation"
      - "div.moduletable"
```

### 10.1 Bootstrap / seed strategy

A new project is initialized by:

1. Fetching the site's `sitemap.xml` if one exists, filtering URLs to the primary domain and to documentation path prefixes.
2. Merging with the manually-provided `seed_urls`.
3. Running a single pass in `DRY_RUN` mode: every URL is fetched and extracted, but nothing is written to containers. A discovery report is produced so the operator can review the URL list before committing.

For SIAT specifically, a sitemap is not reliably published; the seed URL list is authored manually by the operator from the site's menu structure.

---

## 11. Operational Flow per Run

1. Load project configuration and upsert `projects` / `topic_rules`.
2. Fetch and cache `robots.txt` per domain.
3. Select the set of active URLs to evaluate.
4. For each URL (respecting rate limits):
   a. Level 0 precheck.
   b. Conditional GET.
   c. If `200`, extract (Level 2), compute content hash.
   d. Compare to stored hash; classify as `UNCHANGED`, `CHANGED`, `FAILED`, or `NEEDS_REVIEW`.
5. Update SQLite state.
6. Determine which containers are affected by changes.
7. For each affected container, recompute state (`ACTIVE`/`WARM`/.../`SPLIT_PENDING`).
8. Run rebalance on any `SPLIT_PENDING` containers (deterministic greedy).
9. Reassemble only containers whose unit set or state changed.
10. Compute `assembly_hash_sha256` for each reassembled container; write the `.md` file only if the hash changed.
11. Emit the manifest (Section 12) and run report.

A `--dry-run` flag executes steps 1–8 without writing any container file or modifying state.

---

## 12. Manifest Format

Every run emits a `manifest.json` next to the container files. This is the operator's single source of truth for what to do in NotebookLM.

```json
{
  "schema_version": 1,
  "run_id": "run_2026_04_21_0001",
  "project_id": "siat",
  "started_at": "2026-04-21T14:00:00Z",
  "finished_at": "2026-04-21T14:03:22Z",
  "summary": {
    "urls_evaluated": 142,
    "urls_unchanged": 136,
    "urls_changed": 4,
    "urls_failed": 1,
    "urls_review": 1,
    "containers_rewritten": 2
  },
  "containers": [
    {
      "file_name": "siat_sistema_facturacion_vol_01.md",
      "state": "ACTIVE",
      "action_required": "REPLACE_IN_NOTEBOOKLM",
      "prior_assembly_hash": "sha256:ab12...",
      "new_assembly_hash": "sha256:cd34...",
      "word_count": 187420,
      "char_count": 1124900,
      "units_added": [],
      "units_updated": ["unit_siat_0007", "unit_siat_0031"],
      "units_removed": []
    },
    {
      "file_name": "siat_facturacion_manual_vol_01.md",
      "state": "ACTIVE",
      "action_required": "KEEP_AS_IS",
      "new_assembly_hash": "sha256:ef56...",
      "word_count": 98300,
      "char_count": 589800
    }
  ],
  "review_queue": [
    {
      "source_id": "src_siat_0099",
      "url": "https://siatinfo.impuestos.gob.bo/index.php/some-page",
      "reason": "EXTRACTION_LOW_CONFIDENCE",
      "confidence": 0.42,
      "priority": "NORMAL"
    }
  ],
  "notebook_lm_operator_checklist": [
    "Open the 'SIAT Facturación' notebook in NotebookLM.",
    "Delete the old 'siat_sistema_facturacion_vol_01.md' source.",
    "Upload the new 'siat_sistema_facturacion_vol_01.md' from the output directory.",
    "Leave all other sources untouched."
  ]
}
```

The `notebook_lm_operator_checklist` is generated deterministically from the `containers` array and is plain prose specifically so a non-technical operator can follow it.

---

## 13. NotebookLM Integration (Manual)

This MVP does **not** integrate with NotebookLM programmatically. NotebookLM Standard has no public write API.

### 13.1 Output artifacts per run

- One or more `.md` container files in the output directory.
- `manifest.json` (Section 12).
- `run_report.txt` — human-readable summary.
- `errors.log` — any run-level errors.

### 13.2 Manual operator procedure

1. Open `manifest.json` or `run_report.txt`.
2. For each container whose `action_required` is `REPLACE_IN_NOTEBOOKLM`:
   a. In NotebookLM, locate the source with the matching filename.
   b. Delete it.
   c. Upload the new version from the output directory.
3. For each container in `action_required: ADD_TO_NOTEBOOKLM` (new container), upload it.
4. Containers marked `KEEP_AS_IS` are left untouched.

Because the system emits the **same filename** for a given logical container across runs, NotebookLM's source list stays visually stable from the operator's perspective.

---

## 14. Observability

### 14.1 Metrics recorded per run

- URLs evaluated / unchanged / changed / failed / review.
- Percentage requiring retries.
- Per-domain fetch count and average latency.
- Containers in each state.
- Containers rewritten this run.
- Total run duration.

Metrics are written to the `runs` table and also to `run_report.txt`. No external metrics backend in MVP.

### 14.2 Alerting (log-based)

The run exits with a non-zero status and logs a `WARN` or `ERROR` line when:

- More than 20% of URLs failed in a single domain.
- Any container enters `CRITICAL`.
- The review queue grew by more than 10 items.
- `robots.txt` changed in a way that disallows previously-allowed URLs.

Integration with external alerting (email, Slack, etc.) is left to the operator's cron wrapper in the MVP.

---

## 15. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Word count mismatch with NotebookLM | Conservative thresholds + empirical calibration (Section 5.3). |
| Single runaway URL inflates a container | `OVERSIZED_UNIT` policy (Section 8.3). |
| Transient network failure deletes content | Conservative deletion policy (Section 6.2). |
| Readability extractor misidentifies content | Per-domain `include`/`exclude` selector hints + `NEEDS_REVIEW` fallback. |
| SSL issues on `.gob.bo` sites | Explicit per-project `ssl_verify: false` override, logged on every fetch. |
| Rebalance churns operator's NotebookLM sources | Sticky assignment + greedy moves limited to minimum needed units. |
| SQLite corruption | WAL mode + daily DB file backup via operator cron (out of scope for code). |
| Schema evolution | `schema_migrations` table + refuse-to-start-on-mismatch policy. |

---

## 16. Technology Stack

### 16.1 Language and core libraries (Python)

- `httpx` — HTTP client with HTTP/2 and per-host connection pooling.
- `trafilatura` — used for main content discovery and clean HTML extraction.
- `markdownify` — primary Markdown renderer for high-fidelity tables (GFM).
- `selectolax` — high-performance DOM manipulation for pre-extraction cleaning.
- `sqlite3` (stdlib) with WAL mode — persistence.
- `pyyaml` — project config.
- `urllib.robotparser` (stdlib) — robots.txt.
- `pytest` — tests.

No Playwright. No headless browser. No framework-specific profilers.

### 16.2 Runtime

- Python 3.11+.
- Single-process, asyncio-based fetcher with a small worker pool (default 4 concurrent hosts, 1 request-per-second per host).
- Cron-driven execution (operator responsibility), typically weekly.

### 16.3 Project layout

```
doc-sync/
├── doc_sync/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py           # YAML loader + validation
│   ├── db.py               # SQLite + migrations
│   ├── fetch.py            # httpx + robots + rate limiting
│   ├── extract.py          # trafilatura + selector hints
│   ├── normalize.py        # markdown normalization + hashing
│   ├── bucketing.py        # topic rules + state transitions
│   ├── rebalance.py        # greedy rebalance
│   ├── assemble.py         # container file writer
│   ├── manifest.py         # manifest.json + run_report.txt
│   └── errors.py           # error taxonomy (Section 6.3)
├── migrations/
│   ├── 0001_init.sql
│   └── ...
├── projects/
│   └── siat.yaml
├── output/                 # generated containers + manifest
├── state.db                # SQLite
└── tests/
```

---

## 17. Viability Criteria

The MVP is viable if, at the end of a realistic first run against SIAT:

1. All seed URLs were fetched successfully or classified with a known error code.
2. Generated containers pass empirical calibration (Section 5.3) against NotebookLM (reported word count ≤ our threshold).
3. The operator can replicate the NotebookLM upload procedure from the manifest alone, without inspecting containers.
4. A no-op second run produces **zero** container rewrites (all URLs `UNCHANGED`).
5. A deliberate content change on a single SIAT page produces **exactly one** container rewrite on the next run, with all other containers untouched.

Meeting these five criteria is the acceptance test for the MVP.

---

## 18. Roadmap to v2 (Explicit Deferrals)

The following items were intentionally removed from the MVP. They are parked here so v2 planning can pick them up in order of expected value:

| v2 Feature | Triggered when |
|---|---|
| Playwright headless rendering | First SPA documentation site is requested (Docusaurus, VitePress, Nextra, etc.). |
| Framework profiling (Docusaurus/VitePress/Sphinx/MkDocs) | Multiple SPA sites in the project roster. |
| Browser extension for manual recipe authoring | Selector hints prove insufficient for >10% of target URLs. |
| Advanced multi-objective rebalancing | Greedy rebalance produces churn exceeding 5 moved URLs per run on steady-state projects. |
| Image download and local hosting | NotebookLM RAG quality measurably improves with local images. |
| Automatic canonical deduplication | Operator repeatedly resolves `CANONICAL_DUPLICATE` the same way. |
| External metrics (Prometheus) | More than 5 projects in production. |
| Multi-tenant deployment | System is used by more than one team. |

---

## 19. Corrections Applied from the Original Specification

For traceability, these are the concrete changes from the v0.9 spec:

1. **Hash circular problem — fixed.** `content_hash_sha256` now covers the body only, not the header; definition is explicit (Section 5.2).
2. **Word counting ambiguity — fixed.** Counting algorithm defined, thresholds lowered, empirical calibration step added (Section 5.3).
3. **Cascade ordering inconsistency — dissolved.** Headless rendering and framework profiling removed from MVP; pipeline is now a linear 3-level flow (Section 4).
4. **`HEAD` unreliability — fixed.** `HEAD` removed entirely; conditional `GET` only (Section 4, Level 1).
5. **Deletion policy — made concrete.** 3 consecutive failures over ≥14 days (Section 6.2).
6. **Error taxonomy — enumerated.** CHECK-constrained enum replaces free-text error codes (Section 6.3).
7. **`robots.txt` and rate limiting — added.** Mandatory, with default values (Section 6.4).
8. **Canonical URL handling — specified.** Logged, surfaced in manifest, no auto-dedup (Section 6.5).
9. **Topical vs volumetric bucketing — chosen.** Topic rules drive assignment; volumetric thresholds cap growth only (Section 7.2).
10. **Rebalance algorithm — specified.** Deterministic greedy with defined ordering (Section 8.2).
11. **SQLite concurrency — specified.** WAL mode, single-writer (Section 9).
12. **Schema migrations — added.** `schema_migrations` table (Section 9.1).
13. **Manifest format — specified with example.** JSON schema plus example (Section 12).
14. **Bootstrap strategy — added.** Sitemap + seed URLs + `DRY_RUN` discovery run (Section 10.1).
15. **Determinism claim — softened.** "Logical-content determinism" with stable content hash, not byte-identical assembly (Principle 1).
16. **Recipes — removed.** Replaced with minimal `include`/`exclude` selector hints (Section 4, Level 2).
17. **Browser extension — removed.** Deferred to v2 (Section 18).

Any item in the original document not listed above either survived unchanged or was moved to the v2 roadmap.