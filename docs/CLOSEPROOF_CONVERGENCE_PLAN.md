# CloseProof Convergence Plan

Status: v0.1 planning hub  
Owner: PHI369 Labs / Parallax  
Public-safety rule: use dummy/sample data only in public repos.

## Goal

Turn the existing donor apps into a focused CloseProof MVP without dragging every feature forward.

CloseProof v0.1 is not a broad business suite. It is a proof-of-work receipt flow:

```text
create job -> add photos/notes -> signoff or waiver -> seal -> submit -> reviewer approve/reject -> export PDF/JSON -> verify
```

## Donor repos

### FieldHaven

Role: field-tech cockpit and offline workflow donor.

Salvage:

- mobile/field-first technician UX
- offline queue and sync status ideas
- backup/export/vault behaviors
- audit-log and reliability panel concepts
- launch checklist ideas

Do not migrate yet:

- broad marketplace concepts
- non-closeout dashboards
- AI helper features
- real Field Nation data or customer evidence

Tracking issue: https://github.com/MichaelWave369/FieldHaven/issues/9

### ReceiptRipper

Role: evidence intake, hashing, encrypted blob storage donor.

Salvage first:

- upload endpoint/pattern
- raw byte SHA-256 hashing
- encrypted blob storage pattern
- metadata persistence
- export/wipe controls
- optional OCR as helper, not MVP blocker

CloseProof evidence item shape:

```json
{
  "kind": "photo",
  "evidence_id": "ev_...",
  "sha256": "sha256:...",
  "mime": "image/jpeg",
  "bytes": 123456,
  "tags": ["before", "after", "label", "test_result"],
  "captured_at": "...",
  "hash_timing": "live_capture|legacy_import",
  "source": "camera|upload|field_nation|google_photos"
}
```

Tracking issue: https://github.com/MichaelWave369/ReceiptRipper/issues/5

### BizHaven

Role: later back-office layer, not MVP core.

Salvage later:

- clients/projects records
- invoice attachment workflow
- reports/backup/export
- reviewer/client portal concepts

Defer until after the first live sealed receipt:

- invoice generation
- recurring billing
- CRM/client management
- payment reconciliation
- tax reports
- broad dashboards

Tracking issue: https://github.com/MichaelWave369/BizHaven/issues/3

## CloseProof MVP modules

```text
closeproof/evidence       # upload/hash/store evidence blobs
closeproof/receipts       # receipt lifecycle/state machine
closeproof/verify         # canonical JSON, SHA-256, Ed25519 verification
closeproof/legacy_import  # legacy Field Nation/Google Photos backfill
closeproof/reviewer       # approve/reject reviewer view
closeproof/export         # PDF + JSON export
```

## Receipt lifecycle

```text
DRAFT -> READY -> SEALED -> SUBMITTED -> APPROVED
                                  \-> REJECTED -> AMENDED
```

Rules:

- `seal()` is the irreversible boundary.
- Nothing after `SEALED` is edited.
- Corrections become linked amendment receipts.
- Missing lane-required evidence blocks sealing.
- Public demos must use dummy data only.

## Receipt classes

### LIVE_SEALED

Evidence is captured during the job, hashed at capture, sealed at closeout, signed, and independently verifiable.

### LEGACY_BACKFILL

Evidence is imported from completed work history and hashed during import. It is useful for analysis and case studies, but it must never be marketed as if it was live-sealed at the original job time.

Required label:

```text
LEGACY_BACKFILL — evidence hashed during import, not at original capture.
```

## First lane

Use one narrow lane first:

```text
network_low_voltage.closeout/v0.1
```

Required evidence for first lane:

- before photo
- after photo
- label/photo of rack, plate, device, or circuit identifier where applicable
- short closeout note
- tech signoff
- customer signoff or waiver

## First real success metric

Can a field tech seal a real closeout in under 60 seconds and generate a package a reviewer can trust faster?

Measure:

- seconds-to-seal
- reviewer time-to-approve
- rejection/back-and-forth rate
- payment delay/time-to-payment where available

## Build order

1. Port ReceiptRipper-style evidence intake/hash/store into a CloseProof working branch/repo.
2. Implement receipt lifecycle with immutable `SEALED` boundary.
3. Add canonical JSON + SHA-256 + Ed25519 seal/verify.
4. Wire the existing 30-second VERIFY/TAMPERED demo logic into the product.
5. Add FieldHaven-style offline queue/sync/reliability UX.
6. Build legacy importer for Field Nation rows + Google Photos evidence.
7. After first live sealed receipt, pull BizHaven back-office pieces.

## Guardrails

- No real customer names, addresses, photos, job docs, signatures, invoices, or Field Nation screenshots in public GitHub.
- Public demo data must be fake/synthetic.
- CloseProof does not claim to be a payment processor, legal determination, or dispute-resolution engine.
- Marketing language: "tamper-evident evidence your auditor, counsel, or customer can independently verify."

## Mantra

Ship the receipt flow first. Let the Parallax Proof Kernel fall out of production use, not pre-product perfection.
