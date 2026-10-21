"""Phase 8 verification script — runs all critical checks."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone

print("=" * 55)
print("  Financial News Intelligence Platform — Verification")
print("=" * 55)

errors = []

# ── 1. Database init ──────────────────────────────────────
try:
    from backend.database.database import init_db
    init_db()
    print("[1/6] Database init .............. OK")
except Exception as e:
    print(f"[1/6] Database init .............. FAIL: {e}")
    errors.append("database")

# ── 2. Classification ─────────────────────────────────────
try:
    from backend.agents.classification import classify_article
    r = classify_article({
        "headline": "RBI keeps repo rate unchanged at 6.5 percent to manage inflation",
        "summary": "Reserve Bank of India monetary policy committee decision",
        "url": "https://example.com/rbi"
    })
    assert r["category"] == "Banking", f"Expected Banking, got {r['category']}"
    print(f"[2/6] Classification ............. OK  category={r['category']}  companies={r['companies']}")
except Exception as e:
    print(f"[2/6] Classification ............. FAIL: {e}")
    errors.append("classification")

# ── 3. Priority scoring ───────────────────────────────────
try:
    from backend.agents.priority import score_article
    r2 = score_article({
        "headline": "Union Budget 2026 announced major income tax reforms",
        "summary": "Finance minister presents Union Budget with major policy changes",
        "source": "Reuters",
        "category": "Government Policy",
        "companies": "[]",
        "scraped_time": datetime.now(timezone.utc),
        "published_time": None,
    })
    assert r2["priority_score"] >= 80, f"Expected >=80, got {r2['priority_score']}"
    print(f"[3/6] Priority scoring ........... OK  score={r2['priority_score']}")
except Exception as e:
    print(f"[3/6] Priority scoring ........... FAIL: {e}")
    errors.append("priority")

# ── 4. Cleaning agent ─────────────────────────────────────
try:
    from backend.agents.cleaning import clean_and_deduplicate
    cleaned = clean_and_deduplicate([{
        "headline": "Test headline for dedup verification check",
        "summary": "A proper summary paragraph for the test article",
        "url": "https://example.com/test-unique-verify-99999",
        "source": "Reuters",
    }])
    assert isinstance(cleaned, list)
    print(f"[4/6] Cleaning agent ............. OK  articles_out={len(cleaned)}")
except Exception as e:
    print(f"[4/6] Cleaning agent ............. FAIL: {e}")
    errors.append("cleaning")

# ── 5. FastAPI app loads ──────────────────────────────────
try:
    from backend.main import app
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/api/articles" in routes
    assert "/api/stats" in routes
    assert "/api/export/excel" in routes
    assert "/api/export/pdf" in routes
    print(f"[5/6] FastAPI app ................ OK  routes={len(routes)}")
except Exception as e:
    print(f"[5/6] FastAPI app ................ FAIL: {e}")
    errors.append("fastapi")

# ── 6. Export modules ─────────────────────────────────────
try:
    from backend.exports.excel_export import generate_excel
    from backend.exports.pdf_export import generate_pdf
    buf_xl = generate_excel([])
    buf_pdf = generate_pdf([], "none")
    assert buf_xl.read(4) == b"PK\x03\x04"  # xlsx magic bytes
    assert buf_pdf.read(4) == b"%PDF"        # pdf magic bytes
    print("[6/6] Export modules ............. OK  Excel+PDF generated")
except Exception as e:
    print(f"[6/6] Export modules ............. FAIL: {e}")
    errors.append("exports")

# ── Result ────────────────────────────────────────────────
print()
print("=" * 55)
if not errors:
    print("  ALL 6 CHECKS PASSED — Platform is ready.")
else:
    print(f"  {len(errors)} CHECK(S) FAILED: {', '.join(errors)}")
print("=" * 55)
sys.exit(0 if not errors else 1)
