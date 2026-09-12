"""
Contagem de dias uteis (calendario brasileiro simplificado).

INCOMPLETO por desenho: inclui apenas feriados nacionais de data FIXA
(01-01, 21-04, 01-05, 07-09, 12-10, 02-11, 15-11, 25-12) para o ano
corrente e o seguinte. Nao cobre feriados moveis (Carnaval, Sexta-feira
Santa, Corpus Christi), pontos facultativos, feriados estaduais/municipais
nem suspensoes judiciais. Use apenas como auxilio; confirme no tribunal.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Optional, Set

# MM-DD of fixed national holidays (no movable feasts).
FIXED_NATIONAL_MMDD: tuple[str, ...] = (
    "01-01",  # Confraternizacao Universal
    "04-21",  # Tiradentes
    "05-01",  # Dia do Trabalho
    "09-07",  # Independencia
    "10-12",  # Nossa Senhora Aparecida
    "11-02",  # Finados
    "11-15",  # Proclamacao da Republica
    "12-25",  # Natal
)

INCOMPLETE_HOLIDAY_NOTE = (
    "Feriados padrao incompletos: apenas datas nacionais fixas do ano "
    "corrente/seguinte. Sem feriados moveis, locais ou suspensoes judiciais."
)


def is_weekend(d: date) -> bool:
    """True se sabado (5) ou domingo (6)."""
    return d.weekday() >= 5


def default_fixed_national_holidays(
    *,
    reference: Optional[date] = None,
) -> Set[date]:
    """
    Conjunto de feriados nacionais de data fixa para o ano de `reference`
    e o ano seguinte. Documentado como incompleto (sem moveis).
    """
    ref = reference or date.today()
    years = (ref.year, ref.year + 1)
    out: Set[date] = set()
    for year in years:
        for mmdd in FIXED_NATIONAL_MMDD:
            month_s, day_s = mmdd.split("-")
            out.add(date(year, int(month_s), int(day_s)))
    return out


def is_business_day(
    d: date,
    holidays: Optional[Iterable[date]] = None,
) -> bool:
    """Dia util = nao fim de semana e nao feriado no conjunto informado."""
    holiday_set = set(holidays) if holidays is not None else set()
    return not is_weekend(d) and d not in holiday_set


def add_business_days(
    start: date,
    days: int,
    holidays: Optional[Set[date]] = None,
) -> date:
    """
    Avanca `days` dias uteis a partir de `start` (o proprio start nao conta).

    - days > 0: avanca para frente
    - days == 0: devolve start inalterado
    - days < 0: recua em dias uteis

    Se `holidays` for None, usa default_fixed_national_holidays(reference=start).
    Se for set vazio, nao aplica feriados (apenas fins de semana).
    """
    if not isinstance(start, date):
        raise TypeError("start must be a date")
    if not isinstance(days, int):
        raise TypeError("days must be int")

    if holidays is None:
        holiday_set = default_fixed_national_holidays(reference=start)
    else:
        holiday_set = set(holidays)

    if days == 0:
        return start

    step = 1 if days > 0 else -1
    remaining = abs(days)
    current = start
    while remaining > 0:
        current = current + timedelta(days=step)
        if is_business_day(current, holiday_set):
            remaining -= 1
    return current


def compute_business_deadline(
    start: date,
    business_days: int,
    holidays: Optional[Set[date]] = None,
) -> dict:
    """
    Calcula vencimento em dias uteis e metadados para a API.

    Returns:
        due_date (ISO), calendar_days_span (int), note (str)
    """
    if business_days < 0:
        raise ValueError("business_days must be >= 0")

    used_default = holidays is None
    holiday_set = (
        default_fixed_national_holidays(reference=start)
        if holidays is None
        else set(holidays)
    )
    due = add_business_days(start, business_days, holiday_set)
    span = (due - start).days
    note_parts = [
        INCOMPLETE_HOLIDAY_NOTE
        if used_default
        else "Calculo com conjunto de feriados informado pelo chamador."
    ]
    note_parts.append(
        "Contagem exclui sabados, domingos e feriados do conjunto; "
        "confirme no tribunal antes de protocolar."
    )
    return {
        "due_date": due.isoformat(),
        "calendar_days_span": span,
        "note": " ".join(note_parts),
        "start_date": start.isoformat(),
        "business_days": business_days,
    }
