// Frontend URLs
// NOTE: ALL URLs defined in this file must be synced with the frontend URLs defined in src/static/scripts/routes.js

// Python    | JS
// All Caps  | camelCase
// X_Y_Z     | either getXYZ or xYZ

export const routes = {
  getIndexPage: '/',
  getLoginPage: '/login',
  getTaskPanelPage: '/panel',
  getLabelPage: '/label',

  checkPath: '/api/system/check_path',

  checkUsername: '/api/users/check_username',
  loginUser: '/api/users/login',

  createTask: '/api/tasks/create',
  assignTask: '/api/tasks/assign',
  unassignTask: '/api/tasks/unassign',
  updateTask: '/api/tasks/update',

  annotateTask: '/api/annotations/annotate',
  updateAnnotation: '/api/annotations/update_annotation',
  getNextAnnotation: '/api/annotations/get_next_annotation',
  getAnyAnnotation: '/api/annotations/get_annotation',
  getImage: '/api/annotations/get_image',
};
