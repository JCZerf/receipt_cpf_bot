import pytest

from bot.models import CpfQuery, normalize_birth_date, normalize_cpf


@pytest.mark.parametrize(
    "value",
    ["12345678901", "123.456.789-01", "123 456 789 01", "123.456.789/01"],
)
def test_cpf_masks_are_accepted(value):
    assert normalize_cpf(value) == "12345678901"


@pytest.mark.parametrize("value", ["01011990", "01/01/1990", "01-01-1990", "01.01.1990"])
def test_birth_date_separators_are_accepted(value):
    assert normalize_birth_date(value) == "01011990"


@pytest.mark.parametrize("value", ["123", "123456789012", ""])
def test_cpf_with_wrong_digit_count_is_rejected(value):
    with pytest.raises(ValueError):
        normalize_cpf(value)


@pytest.mark.parametrize("value", ["0101990", "010119900", "abc"])
def test_birth_date_with_wrong_digit_count_is_rejected(value):
    with pytest.raises(ValueError):
        normalize_birth_date(value)


def test_query_normalizes_on_construction():
    query = CpfQuery(cpf="123.456.789-01", birth_date="01/01/1990")
    assert query.cpf == "12345678901"
    assert query.birth_date == "01011990"


def test_query_rejects_invalid_input():
    with pytest.raises(ValueError):
        CpfQuery(cpf="123", birth_date="01/01/1990")
