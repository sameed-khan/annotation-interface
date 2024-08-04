// Frontend URLs
// NOTE: ALL URLs defined in this file must be synced with the frontend URLs defined in src/static/scripts/routes.js

// Python    | JS
// All Caps  | camelCase
// X_Y_Z     | either getXYZ or xYZ

export const routes = {
    getIndexPage: '/',
    getLoginPage: '/login',
    getTaskPanelPage: '/panel',    

    checkPath: '/api/system/check_path',

    checkUsername: '/api/users/check_username',
    loginUser: '/api/users/login',

    createTask: '/api/tasks/create',
    assignTask: '/api/tasks/assign',
    unassignTask: '/api/tasks/unassign',
}