from pathlib import Path

from bot.browser.session import PROFILE_PREFIX, session_profile
from bot.config import settings


def test_profile_lives_under_the_configured_root():
    with session_profile() as profile:
        assert profile.parent == settings.CHROME_PROFILE_ROOT
        assert profile.name.startswith(PROFILE_PREFIX)
        assert profile.is_dir()


def test_each_session_gets_its_own_profile():
    with session_profile() as first, session_profile() as second:
        assert first != second, "perfis compartilhados fazem a segunda sessao abortar no Chrome"
        assert first.is_dir() and second.is_dir()


def test_profile_is_removed_afterwards():
    with session_profile() as profile:
        (profile / "Cookies").write_text("dados da sessao")
        path = profile

    assert not path.exists()


def test_cleanup_survives_a_failure_inside_the_session():
    path: Path | None = None
    try:
        with session_profile() as profile:
            path = profile
            raise RuntimeError("consulta falhou no meio")
    except RuntimeError:
        pass

    assert path is not None
    assert not path.exists()


def test_root_is_created_when_missing(monkeypatch, tmp_path):
    root = tmp_path / "nao-existe-ainda"
    monkeypatch.setattr(settings, "CHROME_PROFILE_ROOT", root)

    with session_profile() as profile:
        assert profile.parent == root
