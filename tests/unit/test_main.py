from jeongsimulator import main


def test_main_prints_ready(capsys) -> None:
    """The default CLI should announce readiness and exit."""

    main()

    captured = capsys.readouterr()
    assert "JeongSimulator ready." in captured.out
