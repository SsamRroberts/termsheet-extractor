# 📄 Structured Product Ingestion Exercise

---

## 🧩 Context

We are building an internal infrastructure to:

* Ingest structured product documentation (Termsheets)
* Extract relevant product data
* Validate the data
* Store it in a PostgreSQL database

This exercise simulates a simplified version of that workflow.

### You are provided with:

* **Factsheet (PDF)**
  For your understanding only.
  ❗ Do **not** use it for extraction or validation.

* **Termsheet (PDF)**
  The document describing the product (this is the source of truth).

* **Excel file**
  Contains 3 database tables representing the target schema.

---

## 🎯 Objective

Build a small **Python-based system** that:

1. Extracts required structured data from the documents
2. Outputs structured JSON
3. Validates the extracted data
4. Inserts approved data into PostgreSQL

   * (SQLite is acceptable if PostgreSQL is unavailable)

### ✅ Bonus

Provide **2–3 improvements** you would make to this workflow in a production setting.

You may use any commercial GPT/LLM of your choice to assist with extraction.

---

## 🔒 Constraints

* Python is required
* Use PostgreSQL if possible
* Keep the solution simple and pragmatic
* No full frontend UI required
* Time limit: ~3 hours
* Please do not over-engineer

---

## 📌 Scope of Required Data

All required data fields are contained in the provided spreadsheet.

---

## 🧱 Database Requirements

You are provided with the target table structure in Excel.

Your tasks:

1. Create the 3 PostgreSQL tables
2. Map extracted data into the correct structure
3. Insert data only **after successful validation**

Use appropriate:

* Data types
* Primary keys
* Foreign keys (where relevant)

---

## 🔎 Validation Requirements

Before inserting into the database, your system must:

* Validate extracted data
* Clearly display validation results
* Prevent insertion if validation fails

### Minimum validation rules:

* Valid ISIN format check
* Issue Date < Maturity Date
* At least one underlying present
* Barriers within logical range (if applicable)
* No duplicate product insertion

> The Factsheet is for your own understanding only.
> Validation must rely exclusively on the Termsheet.

---

## 📤 Output Requirements

Your system must:

* Produce structured JSON output before insertion
* Clearly print validation results
* Insert clean data into PostgreSQL

---

## 📦 Deliverables

Please submit:

* Python project (GitHub repo or zip file)
* SQL schema (or migration files)
* README including:

  * How to run the project
  * Assumptions made
  * How GPT was used (if applicable)
  * What you would improve in a production system

---

## 🧠 What We Are Looking For

Strong submissions will demonstrate:

* Sensible data modelling
* Explicit validation logic
* Clean, readable Python code
* Thoughtful GPT usage
* Pragmatic design decisions

---

## 🔄 Follow-Up

After submission, we may provide a second termsheet to test adaptability.

Your system should be reasonably extendable without major rewrites.
