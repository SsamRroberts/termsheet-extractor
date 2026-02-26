"""Test the extraction pipeline against reference values from the Excel file.

The Excel file (data/XS3184638594_data tables.xlsx) is the source of truth.
These tests verify:
  1. Excel data loads cleanly into the application's Pydantic models
  2. Product, underlying, and event fields match expected values
  3. Business-rule validation passes on the reference data
  4. (Integration) LLM extraction from the markdown matches the Excel
"""

import os
from datetime import date

import pytest

from schemas.termsheet import TermsheetData
from services.pipeline.validate import _check_isin_format, _check_isin_luhn, validate_termsheet

# ── Expected constants (from the Excel) ───────────────────────────────────────

EXPECTED_ISIN = "XS3184638594"
EXPECTED_SEDOL = "BVVJPF2"
EXPECTED_ISSUER = "BBVA"
EXPECTED_CURRENCY = "GBP"
EXPECTED_ISSUE_DATE = date(2026, 2, 2)
EXPECTED_MATURITY = date(2032, 2, 2)
EXPECTED_PRODUCT_TYPE = "Phoenix Autocall"
EXPECTED_SHORT_DESC = "6Y FTSE / Eurostoxx Phoenix 8.15% Note"

EXPECTED_UNDERLYINGS = [
    {"bbg_code": "UKX Index", "initial_price": 10148.85},
    {"bbg_code": "SX5E Index", "initial_price": 5957.8},
]

EXPECTED_EVENT_COUNTS = {
    "strike": 1,
    "coupon": 24,
    "auto_early_redemption": 5,
    "knock_in": 1,
}
EXPECTED_TOTAL_EVENTS = 31  # 1 + 23 + 6 + 1

EXPECTED_COUPON_BARRIER = 75.0
EXPECTED_COUPON_AMOUNT = 2.0375
EXPECTED_AUTOCALL_TRIGGER = 100.0
EXPECTED_KNOCKIN_BARRIER = 65.0


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Excel data loads into Pydantic models
# ═══════════════════════════════════════════════════════════════════════════════


class TestExcelDataLoading:
    """Verify the Excel can be parsed into TermsheetData without errors."""

    def test_termsheet_data_is_valid(self, excel_termsheet: TermsheetData):
        assert excel_termsheet is not None

    def test_product_is_populated(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.product_isin == EXPECTED_ISIN

    def test_underlyings_loaded(self, excel_termsheet: TermsheetData):
        assert len(excel_termsheet.underlyings) == len(EXPECTED_UNDERLYINGS)

    def test_events_loaded(self, excel_termsheet: TermsheetData):
        assert len(excel_termsheet.events) == EXPECTED_TOTAL_EVENTS


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Product fields
# ═══════════════════════════════════════════════════════════════════════════════


class TestProductFields:
    def test_isin(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.product_isin == EXPECTED_ISIN

    def test_sedol(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.sedol == EXPECTED_SEDOL

    def test_issuer(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.issuer == EXPECTED_ISSUER

    def test_currency(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.currency == EXPECTED_CURRENCY

    def test_issue_date(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.issue_date == EXPECTED_ISSUE_DATE

    def test_maturity(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.maturity == EXPECTED_MATURITY

    def test_product_type(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.product_type == EXPECTED_PRODUCT_TYPE

    def test_short_description(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.short_description == EXPECTED_SHORT_DESC


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Underlyings
# ═══════════════════════════════════════════════════════════════════════════════


class TestUnderlyings:
    def test_count(self, excel_termsheet: TermsheetData):
        assert len(excel_termsheet.underlyings) == 2

    @pytest.mark.parametrize("idx,expected", list(enumerate(EXPECTED_UNDERLYINGS)))
    def test_bbg_code(self, excel_termsheet: TermsheetData, idx: int, expected: dict):
        assert excel_termsheet.underlyings[idx].bbg_code == expected["bbg_code"]

    @pytest.mark.parametrize("idx,expected", list(enumerate(EXPECTED_UNDERLYINGS)))
    def test_initial_price(self, excel_termsheet: TermsheetData, idx: int, expected: dict):
        assert excel_termsheet.underlyings[idx].initial_price == pytest.approx(
            expected["initial_price"], abs=0.01
        )

    def test_weights_are_null(self, excel_termsheet: TermsheetData):
        for u in excel_termsheet.underlyings:
            assert u.weight is None


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Events
# ═══════════════════════════════════════════════════════════════════════════════


class TestEvents:
    def test_total_count(self, excel_termsheet: TermsheetData):
        assert len(excel_termsheet.events) == EXPECTED_TOTAL_EVENTS

    def test_event_type_counts(self, excel_termsheet: TermsheetData):
        counts: dict[str, int] = {}
        for e in excel_termsheet.events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        assert counts == EXPECTED_EVENT_COUNTS

    def test_coupon_barrier_levels(self, excel_termsheet: TermsheetData):
        coupons = [e for e in excel_termsheet.events if e.event_type == "coupon"]
        for c in coupons:
            assert c.event_level_pct == EXPECTED_COUPON_BARRIER

    def test_coupon_amounts(self, excel_termsheet: TermsheetData):
        coupons = [e for e in excel_termsheet.events if e.event_type == "coupon"]
        for c in coupons:
            assert c.event_amount == pytest.approx(EXPECTED_COUPON_AMOUNT)

    def test_coupon_payment_dates_present(self, excel_termsheet: TermsheetData):
        coupons = [e for e in excel_termsheet.events if e.event_type == "coupon"]
        for c in coupons:
            assert c.event_payment_date is not None
            assert c.event_payment_date > c.event_date

    def test_autocall_trigger_levels(self, excel_termsheet: TermsheetData):
        autocalls = [e for e in excel_termsheet.events if e.event_type == "auto_early_redemption"]
        for a in autocalls:
            assert a.event_level_pct == EXPECTED_AUTOCALL_TRIGGER

    def test_autocall_payment_dates_present(self, excel_termsheet: TermsheetData):
        autocalls = [e for e in excel_termsheet.events if e.event_type == "auto_early_redemption"]
        for a in autocalls:
            assert a.event_payment_date is not None

    def test_knockin_barrier(self, excel_termsheet: TermsheetData):
        knockins = [e for e in excel_termsheet.events if e.event_type == "knock_in"]
        assert len(knockins) == 1
        assert knockins[0].event_level_pct == EXPECTED_KNOCKIN_BARRIER

    def test_strike_event(self, excel_termsheet: TermsheetData):
        strikes = [e for e in excel_termsheet.events if e.event_type == "strike"]
        assert len(strikes) == 1
        assert strikes[0].event_level_pct == 100.0
        assert strikes[0].event_strike_pct == 100.0
        assert strikes[0].event_date == date(2026, 1, 26)

    def test_first_coupon_date(self, excel_termsheet: TermsheetData):
        coupons = sorted(
            [e for e in excel_termsheet.events if e.event_type == "coupon"],
            key=lambda e: e.event_date,
        )
        assert coupons[0].event_date == date(2026, 4, 27)
        assert coupons[0].event_payment_date == date(2026, 5, 5)

    def test_last_coupon_date(self, excel_termsheet: TermsheetData):
        coupons = sorted(
            [e for e in excel_termsheet.events if e.event_type == "coupon"],
            key=lambda e: e.event_date,
        )
        assert coupons[-1].event_date == date(2032, 1, 26)
        assert coupons[-1].event_payment_date == date(2032, 2, 2)

    def test_autocall_dates_are_annual(self, excel_termsheet: TermsheetData):
        """Autocalls should occur roughly once per year (in January)."""
        autocalls = sorted(
            [e for e in excel_termsheet.events if e.event_type == "auto_early_redemption"],
            key=lambda e: e.event_date,
        )
        years = [a.event_date.year for a in autocalls]
        assert years == [2027, 2028, 2029, 2030, 2031]

    def test_maturity_event_date(self, excel_termsheet: TermsheetData):
        knockins = [e for e in excel_termsheet.events if e.event_type == "knock_in"]
        assert knockins[0].event_date == date(2032, 1, 26)
        assert knockins[0].event_payment_date == date(2032, 2, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Business-rule validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidation:
    def test_isin_format_valid(self):
        assert _check_isin_format(EXPECTED_ISIN)

    def test_isin_luhn_valid(self):
        assert _check_isin_luhn(EXPECTED_ISIN)

    def test_isin_format_rejects_bad_isin(self):
        assert not _check_isin_format("INVALID")
        assert not _check_isin_format("XX12345678")  # too short
        assert not _check_isin_format("1234567890AB")  # starts with digits

    def test_isin_luhn_rejects_bad_check_digit(self):
        # Change last digit to break checksum
        bad_isin = EXPECTED_ISIN[:-1] + ("0" if EXPECTED_ISIN[-1] != "0" else "1")
        assert not _check_isin_luhn(bad_isin)

    def test_excel_data_passes_validation(self, excel_termsheet: TermsheetData, mock_db_session):
        result = validate_termsheet(excel_termsheet, mock_db_session)
        errors = [i for i in result.issues if i.severity == "error"]
        assert result.is_valid, f"Validation errors: {[e.message for e in errors]}"

    def test_no_barrier_out_of_range(self, excel_termsheet: TermsheetData, mock_db_session):
        result = validate_termsheet(excel_termsheet, mock_db_session)
        barrier_issues = [i for i in result.issues if i.rule == "barrier_range"]
        assert len(barrier_issues) == 0

    def test_issue_before_maturity(self, excel_termsheet: TermsheetData):
        assert excel_termsheet.product.issue_date < excel_termsheet.product.maturity

    def test_events_within_lifetime(self, excel_termsheet: TermsheetData, mock_db_session):
        """Check whether any events fall outside the product lifetime (warnings)."""
        result = validate_termsheet(excel_termsheet, mock_db_session)
        lifetime_warnings = [i for i in result.issues if i.rule == "event_within_lifetime"]
        # The strike date (2026-01-26) is before issue_date (2026-02-02), so we
        # expect warnings for events that pre-date the issue.
        for w in lifetime_warnings:
            assert w.severity == "warning"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Integration: LLM extraction vs Excel (requires LLM_API_KEY)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("LLM_API_KEY"),
    reason="LLM_API_KEY not set — skipping LLM integration tests",
)
class TestLLMExtractionAgainstExcel:
    """Run the actual LLM extraction on the markdown and compare to Excel.

    These tests are slow and require a running LLM. Skip by default:
        pytest -m "not integration"

    Run explicitly:
        LLM_API_KEY=... pytest -m integration
    """

    @pytest.fixture(autouse=True)
    def _require_markdown(self, markdown_text):
        if markdown_text is None:
            pytest.skip("Markdown file not found — cannot run integration tests")

    @pytest.fixture(scope="class")
    def extracted(self, markdown_text) -> TermsheetData | None:
        if markdown_text is None:
            return None
        from services.llm import extract_termsheet_data

        return extract_termsheet_data(markdown_text)

    def test_product_isin_matches(self, extracted: TermsheetData):
        assert extracted.product.product_isin == EXPECTED_ISIN

    def test_product_dates_match(self, extracted: TermsheetData):
        assert extracted.product.issue_date == EXPECTED_ISSUE_DATE
        assert extracted.product.maturity == EXPECTED_MATURITY

    def test_product_currency_matches(self, extracted: TermsheetData):
        assert extracted.product.currency == EXPECTED_CURRENCY

    def test_product_issuer_matches(self, extracted: TermsheetData):
        assert extracted.product.issuer == EXPECTED_ISSUER

    def test_underlying_count_matches(self, extracted: TermsheetData):
        assert len(extracted.underlyings) == len(EXPECTED_UNDERLYINGS)

    def test_underlying_prices_match(self, extracted: TermsheetData):
        extracted_by_bbg = {u.bbg_code.upper(): u for u in extracted.underlyings}
        for expected in EXPECTED_UNDERLYINGS:
            key = expected["bbg_code"].upper()
            assert key in extracted_by_bbg, f"Missing underlying: {key}"
            assert extracted_by_bbg[key].initial_price == pytest.approx(
                expected["initial_price"], rel=0.01
            )

    def test_event_count_matches(self, extracted: TermsheetData):
        assert len(extracted.events) == EXPECTED_TOTAL_EVENTS

    def test_coupon_count_matches(self, extracted: TermsheetData):
        coupons = [e for e in extracted.events if e.event_type == "coupon"]
        assert len(coupons) == EXPECTED_EVENT_COUNTS["coupon"], (
            f"Expected {EXPECTED_EVENT_COUNTS['coupon']} coupons, got {len(coupons)}"
        )

    def test_autocall_count_matches(self, extracted: TermsheetData):
        autocalls = [
            e for e in extracted.events if e.event_type == "auto_early_redemption"
        ]
        assert len(autocalls) == EXPECTED_EVENT_COUNTS["auto_early_redemption"], (
            f"Expected {EXPECTED_EVENT_COUNTS['auto_early_redemption']} autocalls, got {len(autocalls)}"
        )

    def test_coupon_amounts_match(self, extracted: TermsheetData):
        coupons = [e for e in extracted.events if e.event_type == "coupon"]
        for c in coupons:
            assert c.event_amount == pytest.approx(EXPECTED_COUPON_AMOUNT, rel=0.01)

    def test_coupon_barriers_match(self, extracted: TermsheetData):
        coupons = [e for e in extracted.events if e.event_type == "coupon"]
        for c in coupons:
            assert c.event_level_pct == pytest.approx(EXPECTED_COUPON_BARRIER, rel=0.01)

    def test_extracted_data_passes_validation(
        self, extracted: TermsheetData, mock_db_session
    ):
        result = validate_termsheet(extracted, mock_db_session)
        errors = [i for i in result.issues if i.severity == "error"]
        assert result.is_valid, f"Validation errors: {[e.message for e in errors]}"
