from litestar import Litestar

from app.config import get_settings

settings = get_settings()


async def backup_database() -> None:
    """Check for and create backup of sqlite database on application shutdown"""
    import sqlite3
    from pathlib import Path
    from urllib.parse import urlparse

    if not settings.db.BACKUP:
        return

    database_url = settings.db.URL
    dbname = urlparse(database_url).path
    current_path = Path().resolve()
    dbpath = current_path / Path(dbname)
    backup_path = f"{dbpath}.bak"

    with sqlite3.connect(dbpath) as conn:
        try:
            with sqlite3.connect(backup_path) as backup_conn:
                conn.backup(backup_conn)
        except sqlite3.Error as e:
            print(f"Backup failed: {e}")


def create_app() -> Litestar:
    """Create the litestar application from configured values"""
    from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin

    from app.config.plugin_config import (
        AppDirCLIPlugin,
        alchemy_config,
        session_auth,
        static_files_router,
        template_config,
    )
    from app.domain.controllers import (
        AnnotationController,
        PageController,
        SystemController,
        TaskController,
        UserController,
    )

    return Litestar(
        debug=settings.app.DEBUG,
        route_handlers=[
            PageController,
            UserController,
            SystemController,
            TaskController,
            AnnotationController,
            static_files_router,
        ],
        plugins=[SQLAlchemyPlugin(alchemy_config), AppDirCLIPlugin(settings.cli)],
        template_config=template_config,
        on_app_init=[session_auth.on_app_init],
        middleware=[session_auth.middleware],
        on_shutdown=[backup_database],
    )


app = create_app
