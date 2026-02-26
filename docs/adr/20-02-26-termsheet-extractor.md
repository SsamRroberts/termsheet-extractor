# 001 Initial architectural choices: termsheet extractor (20-02-26)

## Proposed workflow

1. Extract the PDF
2. Dump the extracted PDF to blobstore (fakeblobstore at the moment just somewhere locally)
3. Put data from extracted PDF into LLM to extract values
4. Validate Extraction
  - ISIN format (2-letter country + 9 alphanumeric + 1 check digit, Luhn on alpha-converted string)
  - issue_date < maturity_date
  - At least one underlying
  - Barriers in range: coupon barrier (75%) and knock-in barrier (65%) should be 0-100%
  - No duplicate ISIN in the DB
  - Production difference: Pydantic models for schema validation, cross-field validation (e.g. event dates within product lifetime), reconciliation against source document.
4. Write extraction & metadata to DB with approved = False
5. Display to user to get approved = True

## Tech Stack

1. PDF Extraction [pymupdf4llm](https://github.com/pymupdf/PyMuPDF4LLM) vs [pdfplummer](https://github.com/jsvine/pdfplumber). pymupdf4llm outputs markdown, which can be directly inputted into LLMs whereas pdfplumber exposes pdf objects which would require additional processing to build a extraction pipeline. However pymupdf4llm has an APGL hence, in production, a refactor to pdfplumber will be required to avoid copyleft.
2. Usage of LLM. Allows me to reuse [code](https://github.com/SsamRroberts/49er) for structured output generation. Later in the project more deterministic extraction from pdfplumber objects could be implemented, but for now this is quick.
3. LLM - Kimi instruct for effective tool orchestration. Using a large context model and attempting to "oneshot" would increase risk of halloucinations.

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Options

What have we considered? Pros & Cons?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

