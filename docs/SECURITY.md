# GroundCheck AI — Security Architecture & Safety Invariants

**Version:** 1.0.0  
**Status:** Validated (100% Adversarial Test Pass)  
**Scope:** Trust Boundaries, Adversarial Defenses, and Formal System Invariants

---

## 1. Threat Model & Adversarial Landscape

Environmental impact assessments often govern multi-million-dollar extraction permits, infrastructure projects, and conservation corridors. Consequently, automated audit systems are exposed to specific adversarial threats:

1. **Prompt Injection & LLM Jailbreaking:** Maliciously crafted report text attempting to trick an LLM verifier into declaring false claims compliant.
2. **Topological Spoofing:** Supplying malformed, self-intersecting ("bow-tie") or inverted polygons to artificially inflate or shrink buffer distances and permitted land areas.
3. **Dimensional & Unit Obfuscation:** Submitting non-standard or incompatible units (e.g., claiming compliance by comparing concentration $\mu\text{g/m}^3$ directly to volume $\text{m}^3$).
4. **Regulatory Staleness Exploitation:** Citing superseded or expired standards to claim compliance under outdated emission ceilings.
5. **Storage Tampering:** Modifying evidence files on disk post-audit to manipulate findings retrospectively.
6. **Algorithmic Denial of Service (DoS):** Uploading excessively complex geometries (>10,000 vertices) or zip bombs to exhaust CPU and memory resources.
7. **Benchmark / Data Poisoning:** Attempting to force real user uploads to inherit pre-computed benchmark claims to fake high pass rates.

---

## 2. The Ten Safety Invariants

GroundCheck AI enforces ten mathematically and programmatically verified safety invariants across its entire architecture:

### Invariant 1: No Unverified External Authority
> *Large Language Models and external generative APIs shall never have decision authority over verification outcomes.*
- **Enforcement:** Verification findings (`VERIFIED`, `INCONSISTENT`, `UNVERIFIABLE`) are produced exclusively by deterministic Python algorithms (`Shapely`, geodesic calculations, direct numeric inequality checks). LLMs are strictly confined to unstructured text extraction.

### Invariant 2: Explicit Conflict Precedence
> *When two authoritative ground-truth sources or regulatory standards conflict, the system shall never auto-verify a claim.*
- **Enforcement:** The conflict resolution engine flags the contradiction as `requires_human_confirmation` and halts automatic verification until resolved by an accredited auditor.

### Invariant 3: Deterministic Unit & Dimension Normalization
> *Values with incompatible physical dimensions or unconvertible units shall be strictly rejected from verification.*
- **Enforcement:** The unit normalization engine verifies physical dimension equality (e.g., Area to Area, Concentration to Concentration). Incompatible comparisons trigger an immediate `INCOMPATIBLE_DIMENSIONS` rejection.

### Invariant 4: Topological & Geometrical Validity
> *Geospatial geometries must satisfy strict topological validity before area, distance, or buffer calculations occur.*
- **Enforcement:** Every uploaded GeoJSON/geometry is validated via `shapely.is_valid`. Self-intersecting polygons ("bow-tie" geometries), inverted rings, and non-closed rings are rejected with explicit error diagnostics. Polygons with $>10,000$ vertices are rejected to mitigate algorithmic DoS.

### Invariant 5: Temporal Boundary & Staleness Enforcement
> *Regulatory standards or environmental baselines with a superseded or expiration date in the past shall reject automatic verification.*
- **Enforcement:** Source metadata includes retrieval dates and superseded timestamps. Superseded standards are marked `TEMPORAL_STATUS_EXPIRED`, preventing greenwashing under defunct regulations.

### Invariant 6: Workspace Evidence Immutability
> *All evidence items ingested into the Evidence Workspace are append-only and immutable.*
- **Enforcement:** Every evidence item is assigned a cryptographic SHA-256 content hash upon upload. Updates create new versioned items (`v2`, `v3`) with explicit parent references; historical versions are never overwritten.

### Invariant 7: Disk-level Tamper Detection
> *Any discrepancy between on-disk evidence bytes and their recorded cryptographic hash shall immediately invalidate the verification state.*
- **Enforcement:** The security integrity service re-hashes evidence files from disk during every audit review. If a file was altered or corrupted, the system raises an `INTEGRITY_TAMPER_DETECTED` alert and marks the finding `UNVERIFIABLE`.

### Invariant 8: Benchmark Provenance Isolation
> *Real user document uploads shall never inherit, seed, or cross-contaminate benchmark claims or pre-computed findings.*
- **Enforcement:** Ingestion flags user uploads as `is_benchmark=False`. Benchmark seeding endpoints (`/seed-benchmark`) explicitly enforce `is_benchmark=True` or reject invocation on non-benchmark audits.

### Invariant 9: Tenant & Audit Isolation
> *No audit operation may access, query, link, or mutate evidence belonging to a separate audit workspace.*
- **Enforcement:** All database queries, repository Lookups, and file storage directories enforce strict `audit_id` scoping. Cross-audit ID path manipulation returns HTTP 404/403.

### Invariant 10: Monotonic Risk & Clamped Decision Space
> *Composite risk scores shall be strictly bounded in $[0.0, 100.0]$ and follow explainable monotonic point adjustments.*
- **Enforcement:** The risk calculation engine applies bounded point adjustments ($+5.0\text{ pts}$ per material gap, $-5.0\text{ pts}$ per verified mitigation). Values below 0 or above 100 are clamped, and every single point is traced in machine-readable `contributions`.

---

## 3. Adversarial Attack Verification Suite

The backend test suite (`backend/tests/test_phase9_adversarial.py`) systematically tests the system against simulated real-world adversarial attacks:

| Attack Vector | Test Case | Expected Outcome | Result |
| :--- | :--- | :--- | :--- |
| **Self-Intersecting Bowtie** | `test_01_bowtie_polygon_rejection` | Rejected as `is_valid: False` | **PASS** |
| **Coordinate Out-of-Bounds** | `test_04_coordinate_bounds_clamping` | Latitude $>90^\circ$ rejected | **PASS** |
| **Path Traversal Upload** | `test_16_file_upload_security` | `../../etc/passwd` sanitized | **PASS** |
| **Executable Binary Upload** | `test_16_file_upload_security` | `.exe` rejected with HTTP 400 | **PASS** |
| **Zip Bomb Decompression** | `test_17_zip_bomb_and_archive_security` | Decompression limit enforced | **PASS** |
| **Excessive Geometry Vertices** | `test_18_resource_limits_denial_of_service` | $>10,000$ vertices rejected | **PASS** |
| **Disk Byte Mutation** | `test_13_extended_cryptographic_tamper` | Tamper alert triggered | **PASS** |
| **Dimension Incompatibility** | `test_05_incompatible_unit_rejection` | Area vs Volume rejected | **PASS** |

