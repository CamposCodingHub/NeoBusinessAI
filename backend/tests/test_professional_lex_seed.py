"""Playbook profissional e seed Lex (dry-run / carga)."""

from pathlib import Path

from ai.knowledge_packs import (
    PLAYBOOK_PATH,
    load_professional_playbook,
    playbook_exists,
)


def test_professional_playbook_loads_and_is_bounded():
    assert playbook_exists()
    assert PLAYBOOK_PATH.is_file()
    text = load_professional_playbook(2000)
    assert text
    lowered = text.lower()
    assert "grounding" in lowered
    assert "aliquota" in lowered
    assert len(text) <= 2010  # 2000 + possible ellipsis
    assert Path(PLAYBOOK_PATH).stat().st_size > 0


def test_seed_professional_lex_examples_dry_run_count():
    from scripts.seed_professional_lex_examples import (
        example_count,
        get_examples,
        seed_examples,
    )

    examples = get_examples()
    assert example_count() == len(examples)
    assert 20 <= example_count() <= 40

    domains = {item["domain"] for item in examples}
    expected = {
        "trabalhista",
        "civel_cpc",
        "tributario",
        "contabil_nbc",
        "societario",
        "escritorio_ops",
    }
    assert expected.issubset(domains)

    for item in examples:
        assert item["instruction"].strip()
        assert item["output_text"].strip()

    result = seed_examples(None, dry_run=True)
    assert result["dry_run"] is True
    assert result["example_count"] == example_count()
    assert result["created_or_existing"] == []
