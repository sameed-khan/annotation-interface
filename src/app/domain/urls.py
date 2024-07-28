# API URLs
# NOTE: ALL URLs defined in this file must be synced with the frontend URLs defined in src/static/scripts/routes.js

# Python    | JS
# All Caps  | camelCase
# X_Y_Z     | either getXYZ or xYZ


# MISC
STATIC_FILE_ENDPOINT = "/static"
SCHEMA_ENDPOINT = "/schema"

# SYSTEM INFORMATION
CHECK_PATH = "/api/system/check_path"

# PAGE URLS
LOGIN_PAGE = "/login"
TASK_PANEL_PAGE = "/panel"
ANNOTATE_PAGE = "/label"

# USER
LOGIN_USER = "/api/users/login"
LOGOUT_USER = "/api/users/logout"
CREATE_USER = "/api/users/create"
CHECK_USERNAME = "/api/users/check_username"

# TASK
CREATE_TASK = "/api/tasks/create"
ASSIGN_TASK = "/api/tasks/assign"
UNASSIGN_TASK = "/api/tasks/unassign"
