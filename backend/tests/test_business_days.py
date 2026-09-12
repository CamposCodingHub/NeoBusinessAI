"""Testes unitarios: dias uteis brasileiros (feriados fixos incompletos)."""

from datetime import date

import pytest

from services.business_days import (
    FIXED_NATIONAL_MMDD,
    INCOMPLETE_HOLIDAY_NOTE,
    add_business_days,
    compute_business_deadline,
    default_fixed_national_holidays,
    is_business_day,
    is_weekend,
)


def test_is_weekend_saturday_sunday():
    assert is_weekend(date(2026, 9, 12)) is True  # Saturday
    assert is_weekend(date(2026, 9, 13)) is True  # Sunday
    assert is_weekend(date(2026, 9, 14)) is False  # Monday


def test_add_business_days_skips_weekend():
    # Friday + 1 business day => Monday
    start = date(2026, 9, 11)  # Friday
    assert add_business_days(start, 1, holidays=set()) == date(2026, 9, 14)


def test_add_business_days_skips_fixed_holiday():
    # 2026-04-20 (Mon) + 1 with Tiradentes 04-21 => Wednesday 04-22
    start = date(2026, 4, 20)
    holidays = {date(2026, 4, 21)}
    assert add_business_days(start, 1, holidays=holidays) == date(2026, 4, 22)


def test_add_business_days_zero_and_negative():
    start = date(2026, 9, 14)
    assert add_business_days(start, 0, holidays=set()) == start
    # Tuesday back 1 business day => Monday
    assert add_business_days(start, -1, holidays=set()) == date(2026, 9, 11)


def test_default_holidays_current_and_next_year_incomplete():
    holidays = default_fixed_national_holidays(reference=date(2026, 6, 1))
    assert date(2026, 1, 1) in holidays
    assert date(2027, 12, 25) in holidays
    # 8 fixed dates * 2 years
    assert len(holidays) == len(FIXED_NATIONAL_MMDD) * 2
    assert "moveis" in INCOMPLETE_HOLIDAY_NOTE.lower() or "incompletos" in INCOMPLETE_HOLIDAY_NOTE.lower()


def test_compute_business_deadline_payload():
    result = compute_business_deadline(date(2026, 9, 11), 5, holidays=set())
    assert result["due_date"] == "2026-09-18"
    assert result["calendar_days_span"] == 7
    assert result["business_days"] == 5
    assert "note" in result and result["note"]


def test_is_business_day_with_holiday():
    assert is_business_day(date(2026, 1, 1), {date(2026, 1, 1)}) is False
    assert is_business_day(date(2026, 1, 2), {date(2026, 1, 1)}) is True
