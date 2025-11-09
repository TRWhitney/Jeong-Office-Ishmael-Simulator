from __future__ import annotations

from jeongsimulator import main


def test_main_runs_smoke_session(capsys) -> None:
    """Non-interactive entrypoint should execute a smoke run and exit."""

    main(interactive=False)

    captured = capsys.readouterr()
    assert "JeongSimulator smoke run complete." in captured.out


def test_main_handles_keyboard_interrupt(monkeypatch, capsys) -> None:
    """Ctrl-C should be caught and yield a friendly message."""

    def boom(*_args, **_kwargs) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("jeongsimulator.cli.run_smoke", boom)

    main(interactive=False)

    captured = capsys.readouterr()
    assert "Interrupted" in captured.out
