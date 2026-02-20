import json
import logging
import os
import tomllib
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from core.config import settings
from core.log import setup_logging
from db.db import get_db, test_database_connection
from db.models.product import Product
from schemas.product import (
    EventOut,
    ExtractionResponse,
    JobCreatedResponse,
    ProductDetail,
    ProductSummary,
    UnderlyingOut,
    ValidationIssueOut,
    ValidationResultOut,
)
from services.blobstore import save_markdown
from services.job_store import create_job, pop_job
from services.pdf_extractor import extract_markdown
from services.persistence import persist_extraction
from services.termsheet_llm import extract_termsheet_data
from services.validation import validate_termsheet

setup_logging()
logger = logging.getLogger(__name__)

# Test database connection before initialising the app
test_database_connection()

fastapp = FastAPI(debug=True)

fastapp.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapp.get("/api/version")
async def get_version():
    """Version endpoint for healthcheck."""
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        version = pyproject_data["project"]["version"]
    except Exception:
        version = "unknown"

    return {"version": version, "status": "ok"}


@fastapp.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@fastapp.post("/api/upload-termsheet", response_model=ExtractionResponse)
async def upload_termsheet(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a termsheet PDF — extract, validate, and persist."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    filename = file.filename or "termsheet.pdf"
    logger.info(f"Received termsheet: {filename} ({len(contents)} bytes)")

    # 1. PDF → markdown
    try:
        markdown_text = extract_markdown(contents, filename=filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 2. Save markdown blob under "pending" before LLM call
    save_markdown("pending", filename, markdown_text)

    # 3. LLM extraction
    try:
        termsheet_data = extract_termsheet_data(markdown_text)
    except Exception as exc:
        logger.error(f"LLM extraction failed: {exc}")
        raise HTTPException(status_code=422, detail=f"LLM extraction failed: {exc}")

    # 4. Re-save under correct ISIN
    blob_path = save_markdown(termsheet_data.product.product_isin, filename, markdown_text)

    # 5. Validate
    validation = validate_termsheet(termsheet_data, db)

    # 6. If validation errors → return 422 with data + validation (no DB write)
    if not validation.is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "filename": filename,
                "size_bytes": len(contents),
                "status": "validation_failed",
                "product_isin": termsheet_data.product.product_isin,
                "approved": False,
                "data": termsheet_data.model_dump(mode="json"),
                "validation": validation.to_dict(),
            },
        )

    # 7. Persist with approved=False
    persist_extraction(termsheet_data, filename, blob_path, "success", db)

    return ExtractionResponse(
        filename=filename,
        size_bytes=len(contents),
        status="extracted",
        product_isin=termsheet_data.product.product_isin,
        approved=False,
        data=termsheet_data.model_dump(mode="json"),
        validation=ValidationResultOut(
            is_valid=validation.is_valid,
            issues=[
                ValidationIssueOut(
                    field=i.field, rule=i.rule, message=i.message, severity=i.severity,
                )
                for i in validation.issues
            ],
        ),
    )


def _sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


@fastapp.post("/api/upload-termsheet-async", response_model=JobCreatedResponse)
async def upload_termsheet_async(
    file: UploadFile = File(...),
):
    """Accept a PDF, store it in memory, and return a job_id immediately."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    filename = file.filename or "termsheet.pdf"
    job_id = create_job(filename, contents)
    logger.info(f"Created async job {job_id} for {filename} ({len(contents)} bytes)")

    return JobCreatedResponse(job_id=job_id, filename=filename, size_bytes=len(contents))


@fastapp.get("/api/extraction-stream/{job_id}")
def extraction_stream(job_id: str, db: Session = Depends(get_db)):
    """SSE endpoint that runs the extraction pipeline and streams progress."""

    job = pop_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or already consumed")

    filename, contents = job

    def generate():
        try:
            # 1. PDF → markdown
            yield _sse_event({"stage": "extracting_pdf", "progress": 15})
            try:
                markdown_text = extract_markdown(contents, filename=filename)
            except ValueError as exc:
                yield _sse_event({"stage": "error", "message": f"PDF extraction failed: {exc}"})
                return

            # 2. Save markdown blob under "pending"
            yield _sse_event({"stage": "saving_blob", "progress": 30})
            save_markdown("pending", filename, markdown_text)

            # 3. LLM extraction (the slow step)
            yield _sse_event({"stage": "llm_extraction", "progress": 50})
            try:
                termsheet_data = extract_termsheet_data(markdown_text)
            except Exception as exc:
                logger.error(f"LLM extraction failed: {exc}")
                yield _sse_event({"stage": "error", "message": f"LLM extraction failed: {exc}"})
                return

            # 4. Re-save under correct ISIN
            blob_path = save_markdown(termsheet_data.product.product_isin, filename, markdown_text)

            # 5. Validate
            yield _sse_event({"stage": "validation", "progress": 80})
            validation = validate_termsheet(termsheet_data, db)

            if not validation.is_valid:
                yield _sse_event({
                    "stage": "validation_failed",
                    "progress": 100,
                    "data": {
                        "filename": filename,
                        "size_bytes": len(contents),
                        "status": "validation_failed",
                        "product_isin": termsheet_data.product.product_isin,
                        "approved": False,
                        "data": termsheet_data.model_dump(mode="json"),
                        "validation": validation.to_dict(),
                    },
                })
                return

            # 6. Persist
            yield _sse_event({"stage": "persisting", "progress": 90})
            persist_extraction(termsheet_data, filename, blob_path, "success", db)

            yield _sse_event({
                "stage": "complete",
                "progress": 100,
                "data": {
                    "filename": filename,
                    "size_bytes": len(contents),
                    "status": "extracted",
                    "product_isin": termsheet_data.product.product_isin,
                    "approved": False,
                    "data": termsheet_data.model_dump(mode="json"),
                    "validation": validation.to_dict(),
                },
            })
        except Exception as exc:
            logger.exception(f"Unexpected error in extraction stream: {exc}")
            yield _sse_event({"stage": "error", "message": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream")


@fastapp.patch("/api/products/{product_isin}/approve")
def approve_product(product_isin: str, db: Session = Depends(get_db)):
    """Set a product's approved flag to True."""
    product = db.query(Product).filter(Product.product_isin == product_isin).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.approved:
        raise HTTPException(status_code=409, detail="Product is already approved")

    product.approved = True
    db.flush()
    return {"product_isin": product_isin, "approved": True}


@fastapp.get("/api/products", response_model=list[ProductSummary])
def list_products(db: Session = Depends(get_db)):
    """List all extracted termsheet products."""
    products = db.query(Product).order_by(Product.issue_date.desc()).all()
    return [
        ProductSummary(
            product_isin=p.product_isin,
            sedol=p.sedol,
            short_description=p.short_description,
            issuer=p.issuer,
            issue_date=p.issue_date,
            currency=p.currency,
            maturity=p.maturity,
            product_type=p.product_type,
            approved=p.approved,
            underlying_count=len(p.underlyings),
            event_count=len(p.events),
        )
        for p in products
    ]


@fastapp.get("/api/products/{product_isin}", response_model=ProductDetail)
def get_product(product_isin: str, db: Session = Depends(get_db)):
    """Get full details for a given extracted termsheet."""
    product = db.query(Product).filter(Product.product_isin == product_isin).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductDetail(
        product_isin=product.product_isin,
        sedol=product.sedol,
        short_description=product.short_description,
        issuer=product.issuer,
        issue_date=product.issue_date,
        currency=product.currency,
        maturity=product.maturity,
        product_type=product.product_type,
        word_description=product.word_description,
        approved=product.approved,
        underlyings=[UnderlyingOut.model_validate(u) for u in product.underlyings],
        events=[
            EventOut.model_validate(e)
            for e in sorted(product.events, key=lambda e: e.event_date)
        ],
    )


# ---------------------------------------------------------------------------
# Serve frontend build (must be AFTER all /api routes)
# ---------------------------------------------------------------------------
frontend_dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

if os.path.exists(frontend_dist_path):
    assets_dir = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_dir):
        fastapp.mount(
            "/assets", StaticFiles(directory=assets_dir), name="assets"
        )


@fastapp.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the SPA for all non-API routes."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Serve static files directly if they exist in the dist folder
    if "." in full_path:
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.exists(file_path):
            return FileResponse(file_path)

    # For all other routes, serve index.html (SPA client-side routing)
    index_path = os.path.join(frontend_dist_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Frontend not found")
