"""Unit tests for business-rule validation (synthetic data, no Excel/LLM)."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from tests.factories import make_event, make_product, make_termsheet, make_underlying, mock_db
from services.pipeline.validate import (
    ValidationResult,
    ValidationIssue,
    _check_isin_format,
    _check_isin_luhn,
    validate_termsheet,
)


# ═══════════════════════════════════════════════════════════════════════════════
# ISIN format checks
# ═══════════════════════════════════════════════════════════════════════════════


class TestISINFormat:
    @pytest.mark.parametrize("isin", [
        "XS3184638594",
        "US0378331005",
        "GB0002634946",
        "DE000BAY0017",
    ])
    def test_valid_isins(self, isin):
        assert _check_isin_format(isin)

    @pytest.mark.parametrize("isin,reason", [
        ("INVALID", "too short, no digits"),
        ("XX12345678", "only 10 chars"),
        ("1234567890AB", "starts with digits"),
        ("xs3184638594", "lowercase letters"),
        ("XS31846385940", "13 chars"),
        ("XS318463859A", "last char not digit"),
        ("", "empty string"),
    ])
    def test_invalid_isins(self, isin, reason):
        assert not _check_isin_format(isin), reason


# ═══════════════════════════════════════════════════════════════════════════════
# ISIN Luhn checks
# ═══════════════════════════════════════════════════════════════════════════════


class TestISINLuhn:
    @pytest.mark.parametrize("isin", [
        "XS3184638594",
        "US0378331005",
        "GB0002634946",
    ])
    def test_valid_checksums(self, isin):
        assert _check_isin_luhn(isin)

    def test_bad_check_digit(self):
        # XS3184638594 is valid; XS3184638595 should fail
        assert not _check_isin_luhn("XS3184638595")

    def test_swapped_digits(self):
        # Swap two adjacent digits — should break checksum
        assert not _check_isin_luhn("XS3184683594")


# ═══════════════════════════════════════════════════════════════════════════════
# validate_termsheet — full rule suite
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidateTermsheet:
    def test_valid_data_passes(self):
        result = validate_termsheet(make_termsheet(), mock_db())
        assert result.is_valid
        errors = [i for i in result.issues if i.severity == "error"]
        assert len(errors) == 0

    # ── isin_format ───────────────────────────────────────────────────────

    def test_bad_isin_format_is_error(self):
        ts = make_termsheet(product=make_product(product_isin="bad-isin"))
        result = validate_termsheet(ts, mock_db())
        assert not result.is_valid
        rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "isin_format" in rules

    # ── isin_luhn ─────────────────────────────────────────────────────────

    def test_bad_isin_luhn_is_error(self):
        # Valid format but bad checksum
        ts = make_termsheet(product=make_product(product_isin="XS3184638595"))
        result = validate_termsheet(ts, mock_db())
        assert not result.is_valid
        rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "isin_luhn" in rules

    def test_bad_format_does_not_trigger_luhn(self):
        ts = make_termsheet(product=make_product(product_isin="BAD"))
        result = validate_termsheet(ts, mock_db())
        rules = {i.rule for i in result.issues}
        assert "isin_format" in rules
        assert "isin_luhn" not in rules

    # ── issue_before_maturity ─────────────────────────────────────────────

    def test_issue_equals_maturity_is_error(self):
        ts = make_termsheet(
            product=make_product(issue_date=date(2026, 2, 2), maturity=date(2026, 2, 2)),
        )
        result = validate_termsheet(ts, mock_db())
        assert not result.is_valid
        rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "issue_before_maturity" in rules

    def test_issue_after_maturity_is_error(self):
        ts = make_termsheet(
            product=make_product(issue_date=date(2032, 2, 2), maturity=date(2026, 2, 2)),
        )
        result = validate_termsheet(ts, mock_db())
        assert not result.is_valid
        rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "issue_before_maturity" in rules

    # ── min_underlyings ───────────────────────────────────────────────────

    def test_no_underlyings_is_error(self):
        ts = make_termsheet(underlyings=[])
        result = validate_termsheet(ts, mock_db())
        assert not result.is_valid
        rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "min_underlyings" in rules

    def test_one_underlying_passes(self):
        ts = make_termsheet(underlyings=[make_underlying()])
        result = validate_termsheet(ts, mock_db())
        assert "min_underlyings" not in {i.rule for i in result.issues}

    # ── barrier_range ─────────────────────────────────────────────────────

    @pytest.mark.parametrize("level", [-1.0, -0.01, 100.01, 200.0])
    def test_barrier_out_of_range_is_error(self, level):
        ts = make_termsheet(events=[make_event(event_type="coupon", event_level_pct=level)])
        result = validate_termsheet(ts, mock_db())
        assert not result.is_valid
        rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "barrier_range" in rules

    @pytest.mark.parametrize("level", [0.0, 50.0, 75.0, 100.0])
    def test_barrier_in_range_passes(self, level):
        ts = make_termsheet(events=[make_event(event_type="coupon", event_level_pct=level)])
        result = validate_termsheet(ts, mock_db())
        assert "barrier_range" not in {i.rule for i in result.issues}

    def test_barrier_check_applies_to_knock_in(self):
        ts = make_termsheet(events=[
            make_event(event_type="knock_in", event_level_pct=150.0, event_date=date(2032, 1, 26)),
        ])
        result = validate_termsheet(ts, mock_db())
        rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "barrier_range" in rules

    def test_barrier_check_ignores_strike_events(self):
        ts = make_termsheet(events=[
            make_event(event_type="strike", event_level_pct=100.0, event_date=date(2026, 1, 26)),
        ])
        result = validate_termsheet(ts, mock_db())
        assert "barrier_range" not in {i.rule for i in result.issues}

    def test_barrier_check_ignores_none_level(self):
        ts = make_termsheet(events=[make_event(event_type="coupon", event_level_pct=None)])
        result = validate_termsheet(ts, mock_db())
        assert "barrier_range" not in {i.rule for i in result.issues}

    # ── duplicate_isin ────────────────────────────────────────────────────

    def test_duplicate_isin_is_error(self):
        existing = MagicMock()
        result = validate_termsheet(make_termsheet(), mock_db(existing_product=existing))
        assert not result.is_valid
        rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "duplicate_isin" in rules

    def test_no_duplicate_passes(self):
        result = validate_termsheet(make_termsheet(), mock_db(existing_product=None))
        assert "duplicate_isin" not in {i.rule for i in result.issues}

    # ── event_within_lifetime ─────────────────────────────────────────────

    def test_event_before_issue_is_warning(self):
        ts = make_termsheet(events=[
            make_event(event_date=date(2026, 1, 1)),  # before issue_date 2026-02-02
        ])
        result = validate_termsheet(ts, mock_db())
        lifetime_issues = [i for i in result.issues if i.rule == "event_within_lifetime"]
        assert len(lifetime_issues) == 1
        assert lifetime_issues[0].severity == "warning"
        # Warnings don't break is_valid
        assert result.is_valid

    def test_event_after_maturity_is_warning(self):
        ts = make_termsheet(events=[
            make_event(event_date=date(2033, 1, 1)),  # after maturity 2032-02-02
        ])
        result = validate_termsheet(ts, mock_db())
        lifetime_issues = [i for i in result.issues if i.rule == "event_within_lifetime"]
        assert len(lifetime_issues) == 1
        assert lifetime_issues[0].severity == "warning"

    def test_event_within_lifetime_no_warning(self):
        ts = make_termsheet(events=[
            make_event(event_date=date(2028, 6, 15)),  # well within lifetime
        ])
        result = validate_termsheet(ts, mock_db())
        assert not any(i.rule == "event_within_lifetime" for i in result.issues)

    def test_event_on_boundaries_no_warning(self):
        ts = make_termsheet(events=[
            make_event(event_date=date(2026, 2, 2)),  # exactly issue_date
            make_event(event_date=date(2032, 2, 2)),  # exactly maturity
        ])
        result = validate_termsheet(ts, mock_db())
        assert not any(i.rule == "event_within_lifetime" for i in result.issues)


# ═══════════════════════════════════════════════════════════════════════════════
# ValidationResult dataclass
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidationResult:
    def test_empty_is_valid(self):
        r = ValidationResult()
        assert r.is_valid
        assert r.to_dict() == {"is_valid": True, "issues": []}

    def test_warning_only_is_still_valid(self):
        r = ValidationResult(issues=[
            ValidationIssue(field="x", rule="test", message="just a warning", severity="warning"),
        ])
        assert r.is_valid

    def test_error_makes_invalid(self):
        r = ValidationResult(issues=[
            ValidationIssue(field="x", rule="test", message="bad", severity="error"),
        ])
        assert not r.is_valid

    def test_to_dict_roundtrip(self):
        r = ValidationResult(issues=[
            ValidationIssue(field="f", rule="r", message="m", severity="error"),
        ])
        d = r.to_dict()
        assert d["is_valid"] is False
        assert len(d["issues"]) == 1
        assert d["issues"][0] == {
            "field": "f", "rule": "r", "message": "m", "severity": "error",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Multiple errors at once
# ═══════════════════════════════════════════════════════════════════════════════


class TestMultipleErrors:
    def test_accumulates_all_errors(self):
        """A termsheet with many problems should report all of them."""
        ts = make_termsheet(
            product=make_product(
                product_isin="BADISIN",
                issue_date=date(2032, 2, 2),
                maturity=date(2026, 2, 2),
            ),
            underlyings=[],
            events=[make_event(event_type="coupon", event_level_pct=150.0)],
        )
        result = validate_termsheet(ts, mock_db())
        error_rules = {i.rule for i in result.issues if i.severity == "error"}
        assert "isin_format" in error_rules
        assert "issue_before_maturity" in error_rules
        assert "min_underlyings" in error_rules
        assert "barrier_range" in error_rules
        assert not result.is_valid
