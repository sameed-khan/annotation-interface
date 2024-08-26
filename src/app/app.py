from litestar import Litestar


def create_app() -> Litestar:
    """Create the litestar application from configured values"""
    from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin

    from app.config import get_settings
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

    settings = get_settings()

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
    )


app = create_app
