# Mostly copied from https://github.com/litestar-org/litestar-fullstack/blob/main/src/app/__main__.py


def run_cli() -> None:
    """Application Entrypoint"""
    import os
    import sys
    from pathlib import Path

    root_dir = Path(__file__).parent.parent.resolve()
    sys.path.append(str(root_dir))
    os.environ.setdefault("LITESTAR_APP", "app.app:app")

    try:
        from litestar.__main__ import run_cli as run_litestar_cli
    except ImportError as exc:
        print(
            "Could not load required libarires. ",
            "Please check your installation and activate any necessary virtual environment",
        )
        print(exc)
        sys.exit(1)
    run_litestar_cli()


if __name__ == "__main__":
    run_cli()
