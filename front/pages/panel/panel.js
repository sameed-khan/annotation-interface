import {routes} from '../../shared/scripts/routes.js';
import {
  FormValidationManager,
  FormValidationControl,
  onlyAlphaNumeric,
  onlyAlphanumericSpacesHyphens,
  onlySingleCharacter,
  allItemsUnique,
  bulmaRemoveDanger,
  bulmaSetDanger,
  partial,
  escapeBackslashes,
  notUndoKey,
} from './validation.js';
import {LabelKeybindInput} from '../../components/label-keybind-input.ts';

// GLOBAL VARIABLES
let lkSelectControls = 2; // the html template always starts with 2 label-keybind select fields

function populateModal(target, taskData) {
  target.querySelector('form').innerHTML = `
        <div class="columns">
            <fieldset name="label-keybind-input-form-group" class="column is-half">
                <label class="label">Edit Labels and Keybinds</label> 
                ${taskData.label_keybinds
                  .map(
                    (lk) => `
                    <div class="field label-keybind-input-field is-flex is-flex-wrap-nowrap mb-1">
                        <div class="control is-flex-grow-1">
                            <input class="input" type="text" value="${lk.label}" required>
                        </div>
                        <div class="control is-flex-grow-0">
                            <div class="select">
                                <select>
                                    ${['A', 'S', 'D', 'F', 'J', 'K', 'L', ';']
                                      .map(
                                        (key) =>
                                          `<option ${key === lk.keybind ? 'selected' : ''}>${key}</option>`
                                      )
                                      .join('')}
                                </select>
                            </div>
                        </div>
                    </div>
                `
                  )
                  .join('')}
            </fieldset>
            <fieldset name="file-select-input-form-group" class="column is-half">
                <label class="label">Select Images to Include</label>
                ${taskData.files
                  .map(
                    (file) => `
                    <div class="field">
                        <div class="control task-file-select-control">
                            <label class="b-checkbox checkbox task-file-select">
                                <input type="checkbox" ${file.included ? 'checked' : ''}>
                                <span class="check is-info"></span>
                                <span class="control-label">${file.name}</span>
                            </label>
                        </div>
                    </div>
                `
                  )
                  .join('')}
            </fieldset>
        </div>
        <div class="field is-grouped">
            <div class="control">
                <button class="button is-link" type="submit">Submit Changes</button>
            </div>
            <div class="control">
                <button class="button is-link is-ghost cancel-close" type="reset">Cancel</button>
            </div>
        </div>
        `;
}

function generateRequestFromTaskCreationForm(formData) {
  /**
   * [                                        {
   *  [root-folder-path, 'path/to/root'],         root: 'path/to/root',
   *                                       =>     label_keybinds: [
   *  [label1, keybind1],                                 {label: 'label1', keybind: 'keybind1'},
   *  [label2, keybind2],                                 {label: 'label2', keybind: 'keybind2'},
   *  ...]                                            ...]
   *                                          }
   */

  let taskData = {
    title: null,
    root: null,
    label_keybinds: [],
  };

  for (const [key, value] of formData.entries()) {
    if (key.startsWith('label-input-')) {
      let lkIndex = key.split('-')[2];
      let lk = taskData.label_keybinds[lkIndex] || {};
      lk.label = value;
      taskData.label_keybinds[lkIndex] = lk;
    } else if (key.startsWith('keybind-input-')) {
      let lkIndex = key.split('-')[2];
      let lk = taskData.label_keybinds[lkIndex] || {};
      lk.keybind = value;
      taskData.label_keybinds[lkIndex] = lk;
    } else if (key === 'root-folder-input') {
      let backSlashEscaped = escapeBackslashes(value);
      taskData.root = encodeURIComponent(backSlashEscaped);
    } else if (key === 'task-title-input') {
      taskData.title = value;
    } else {
      throw new Error('Invalid form data key found: ' + key);
    }
  }

  return taskData;
}

function generateRequestFromTaskAssignmentForm(formData) {
  /**
   * formData: { task-checkbox: [task_id1, task_id2, ...] }
   */

  let taskData = {
    tasks_to_add_ids: formData.values().toArray(),
  };

  return taskData;
}

// EVENT HANDLER FUNCTIONS
function handleTaskCreateModalOpen(event) {
  const modalTrigger = event.target.closest('.js-modal-trigger');
  const m = modalTrigger.dataset.target;
  const target = document.getElementById(m);
  target.showModal();
}

function handleTaskEditModalOpen(event) {
  modalTrigger = event.target.closest('.js-modal-trigger.edit-keybind-button');
  const m = modalTrigger.dataset.target;
  const target = document.getElementById(m);
  fetch(`/panel/get_task_keybinds?task_id=${encodeURIComponent(taskId)}`)
    .then((response) => response.json())
    .then((data) => {
      populateModal(target, data);
      target.showModal();
    })
    .catch((error) => {
      alert('An error occurred while fetching task data. Please contact the developer.');
      console.log(error);
    });
}

function handleTaskDeleteButtonClick(event) {
  const taskId = event.currentTarget.dataset.task_id;
  fetch(`${routes.unassignTask}?task_id=${encodeURIComponent(taskId)}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json();
    })
    .then(() => {
      window.location.reload();
    })
    .catch((error) => {
      console.error(error);
      alert('An error occurred while deleting the task.');
    });
}

async function handleTaskExportButtonClick(event) {
  const taskId = event.currentTarget.dataset.task_id;

  try {
    const response = await fetch(`${routes.exportTask}?task_id=${encodeURIComponent(taskId)}`);
    if (!response.ok) throw new Error(`Download failed: ${response.statusText}`);

    const blob = await response.blob();
    const fileName = response.headers.get('Content-Disposition').split('filename=')[1];

    const url = window.URL.createObjectURL(blob);

    // create a hidden anchor element and click it to download the file
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error(`Download error: ${error}`);
    alert('An error occured while exporting the task.');
  }
}

/**
 *
 * @param {HTMLDialogElement} modal
 * @param {Event} close
 */
function handleModalClose(event) {
  const modal = event.target.closest('dialog');
  const rect = modal.getBoundingClientRect();
  const isInModal =
    rect.top <= event.clientY &&
    event.clientY <= rect.top + rect.height &&
    rect.left <= event.clientX &&
    event.clientX <= rect.left + rect.width;
  if (!isInModal) {
    modal.close();
  }
}

/**
 *
 * @param {HTMLElement} modal_trigger
 * @param {Event} close
 */
/**
 *
 * @param {Event} close
 */
function handleModalCloseByCancel(event) {
  const modal = event.target.closest('dialog');
  modal.close();
  modal.querySelectorAll('.dynamic-inserted-element').forEach((element) => {
    element.remove();
  });
}
/**
 *
 * @param {HTMLElement} triggerElement
 * @param {Event} event
 */
function handleTaskManageModalTabSwitch(event) {
  event.preventDefault();
  event.stopPropagation();

  const targetAnchor = event.target.closest('a.task-manage-modal-trigger');
  const targetTab = event.target.closest('li.task-manage-tab');
  const targetModal = event.target.closest('dialog');
  const targetForm = document.getElementById(targetAnchor.dataset.target);

  targetModal
    .querySelectorAll('li.task-manage-tab')
    .forEach((tab) => tab.classList.remove('is-active'));
  targetTab.classList.add('is-active');

  targetModal.querySelectorAll('form').forEach((form) => form.classList.add('is-hidden'));
  targetForm.classList.remove('is-hidden');
}

function handleAddLabelButtonClick(event) {
  // create a new div
  let newDiv = document.createElement('div');
  let newElementHTML = `
        <div class="field is-grouped label-keybind-input-field dynamic-inserted-element mb-1">
            <div class="control is-expanded">
                <input name="label-input-${lkSelectControls}" class="input label-input" type="text" placeholder="Enter label" required>
            </div>
            <div class="control keybind-control has-text-centered">
                <input name="keybind-input-${lkSelectControls}" class="input keybind-input" autocomplete="off" readonly onfocus="this.removeAttribute('readonly');">
            </div>
        </div>
    `;

  // get the last instance of the above type of element and insert as next sibling
  const controlElementId = event.currentTarget.closest('.control').id;
  let endBoundaryElement = document.querySelector(
    `.dynamic-insert-end-boundary:has(+ #${controlElementId})`
  );
  let parentFieldset = endBoundaryElement.closest('fieldset');
  parentFieldset.insertBefore(newDiv, endBoundaryElement);

  // now that the element is inserted, we can safely change the outerHTML
  newDiv.outerHTML = newElementHTML;

  // increment the lkSelectControls counter
  lkSelectControls++;
}

// document.queryselectorall('.task-display-card .media-content').foreach(content => {
/**
 *
 * @param {HTMLElement} content
 */
function handleTaskCardMouseEvents(event) {
  cardParent = event.target.closest('.task-display-card');
  if (event.type === 'mouseenter') {
    cardParent.style.filter = 'brightness(90%)';
  } else if (event.type === 'mouseleave') {
    cardParent.style.filter = '';
  } else if (event.type === 'click') {
    let url = new URL(window.location.origin);
    url.pathname = '/label';
    url.searchParams.append('task_id', cardParent.dataset.task_id);
    window.location.href = url.href;
  }
}

//.root-folder-input
function handleRootFolderFormValidation(event) {
  let rootFolderInput = document.getElementById('root-folder-input');
  let submitButton = document.getElementById('task-creation-submit-button');
  let invalidRootFolderHelpText = document.getElementById('root-folder-help-text-danger');
  let validRootFolderHelpText = document.getElementById('root-folder-help-text-info');

  fetch(`${routes.checkPath}?path=${encodeURIComponent(rootFolderInput.value)}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json();
    })
    .then((data) => {
      validRootFolderHelpText.textContent = `Found ${data.file_count} files to annotate`;
      validRootFolderHelpText.classList.remove('is-hidden');
      invalidRootFolderHelpText.classList.add('is-hidden');
      submitButton.disabled = false;
    })
    .catch((error) => {
      invalidRootFolderHelpText.textContent = error.message;
      invalidRootFolderHelpText.classList.remove('is-hidden');
      validRootFolderHelpText.classList.add('is-hidden');
      submitButton.disabled = true;
    });
}

// document.getelementbyid('task-creation-form').queryselectorall('input.label-input').foreach(inputelement => {
function handleLabelInputFormValidation(event) {
  const inputElement = event.target; // calling code MUST PASS EXACT EVENT MATCH
  const submitButton = document.getElementById('task-creation-submit-button');
  const labelAlphanumericSpaceHyphenValidation = new FormValidationControl(
    inputElement,
    onlyAlphanumericSpacesHyphens,
    'Only alphanumeric characters, spaces, and hyphens allowed.'
  );

  const labelLessThan20CharsValidation = new FormValidationControl(
    inputElement,
    (value) => value.length <= 20
  );

  const allLabelFields = [
    ...inputElement.closest('fieldset').querySelectorAll('input.label-input'),
  ].map((input) => input.value);

  const labelsUniqueValidation = new FormValidationControl(
    inputElement,
    partial(allItemsUnique, allLabelFields),
    'Labels are case and space insensitive and must be unique.'
  );

  const labelValidationManager = new FormValidationManager(
    bulmaRemoveDanger,
    bulmaSetDanger,
    inputElement.closest('fieldset').querySelector('p.help'),
    submitButton,
    labelAlphanumericSpaceHyphenValidation,
    labelLessThan20CharsValidation,
    labelsUniqueValidation
  );

  labelValidationManager.applyValidation();
}

// capture keypress event for keybind inputs and insert that key into the input field
// document.getelementbyid('task-creation-form').queryselectorall('input.keybind-input').foreach(inputelement => {
function handleKeybindInputFormValidation(event) {
  event.preventDefault();

  const inputElement = event.target;
  inputElement.value = event.key.toUpperCase();
  const helpTextElement = inputElement.closest('fieldset').querySelector('p.help');
  const submitButton = document.getElementById('task-creation-submit-button');

  const otherKeybinds = [
    ...inputElement.closest('fieldset').querySelectorAll('input.keybind-input'),
  ].map((input) => input.value);

  const keybindsUniqueValidation = new FormValidationControl(
    inputElement,
    partial(allItemsUnique, otherKeybinds),
    'Keybinds are case-insensitive and must be unique.'
  );

  const notUndoKeyValidation = new FormValidationControl(
    inputElement,
    notUndoKey,
    '"Z" and "z" are reserved for undo. Please choose another key.'
  );

  const labelValidationManager = new FormValidationManager(
    bulmaRemoveDanger,
    bulmaSetDanger,
    helpTextElement,
    submitButton,
    keybindsUniqueValidation,
    notUndoKeyValidation
  );

  labelValidationManager.applyValidation();

  if (event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) {
    console.log('Modifier key detected');
    inputElement.classList.add('is-danger');
    helpTextElement.textContent =
      'Keybind must not include modifier keys (Shift, Ctrl, Alt, or Meta).';
  }
}

// handle submit event button disabled if label-keybind-input lit component is invalid
function handleTaskUpdateFormValidation(event) {
  const submitButton = document.getElementById('task-edit-form-submit-button');
  submitButton.disabled = event.detail.isValid === false ? true : false;
}

// document.getelementbyid('task-creation-form').addeventlistener('submit', function(event) {
function handleTaskCreationFormSubmit(event) {
  event.preventDefault();
  let formData = new FormData(event.target);
  const formElement = event.target;
  let taskData = generateRequestFromTaskCreationForm(formData);
  fetch(routes.createTask, {
    method: 'POST',
    body: JSON.stringify(taskData),
    headers: {
      'Content-Type': 'application/json',
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json();
    })
    .then(() => {
      window.location.reload();
    })
    .catch((error) => {
      console.error(error);
      formElement.reset();
      alert('An error occurred while creating the task.');
    });
}

function handleTaskAssignmentFormSubmit(event) {
  event.preventDefault();
  let formData = new FormData(event.target); // switching this line with line below causes error
  const formElement = event.target; // not sure why, something to do with FormData expire
  let taskData = generateRequestFromTaskAssignmentForm(formData);
  fetch(routes.assignTask, {
    method: 'POST',
    body: JSON.stringify(taskData),
    headers: {
      'Content-Type': 'application/json',
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json();
    })
    .then(() => {
      window.location.reload();
    })
    .catch((error) => {
      console.error(error);
      formElement.reset();
      alert('An error occurred while creating the task.');
    });
}

function handleTaskUpdateFormSubmit(event) {
  event.preventDefault();
  let formData = new FormData(event.target);
  const formElement = event.target;
  let taskData = generateRequestFromTaskCreationForm(formData);
  fetch(routes.updateTask, {
    method: 'POST',
    body: JSON.stringify(taskData),
    headers: {
      'Content-Type': 'application/json',
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json();
    })
    .then(() => {
      window.location.reload();
    })
    .catch((error) => {
      console.error(error);
      formElement.reset();
      alert('An error occurred while creating the task.');
    });
}

// ALWAYS ORDER MORE SPECIFIC SELECTORS FIRST
const HANDLER_MAP = {
  click: [
    // Modal
    ['.js-modal-trigger', handleTaskCreateModalOpen], // stop propagation tab is within modal
    ['.task-manage-tab', handleTaskManageModalTabSwitch],
    ['.add-label-button', handleAddLabelButtonClick],
    ['.cancel-close', handleModalCloseByCancel],
    ['dialog', handleModalClose],
    // ['.js-modal-trigger.edit-keybind-button', handleTaskEditModalOpen],
    // Panel Main Page
    ['.task-display-card .media-content', handleTaskCardMouseEvents],
    ['.delete-task-button', handleTaskDeleteButtonClick],
    ['.export-task-button', handleTaskExportButtonClick],
  ],
  keydown: [['.keybind-input', handleKeybindInputFormValidation]],
  input: [
    // these selectors are for the EXACT INPUT ELEMENT cannot be for containing box
    ['#root-folder-input', handleRootFolderFormValidation],
    ['.label-input', handleLabelInputFormValidation],
  ],
  submit: [
    ['#task-creation-form', handleTaskCreationFormSubmit],
    ['#task-assign-form', handleTaskAssignmentFormSubmit],
    ['#task-edit-form', handleTaskUpdateFormSubmit],
  ],
  validate: [['label-keybind-input', handleTaskUpdateFormValidation]],
};

// Handle all events via event delegation
// This pattern only allows each click action to trigger one action
// NOTE: Some events trigger MULTIPLE HANDLERS, the ORDER OF HANDLERS in HANDLER_MAP DETERMINES
// THE PRECEDENCE

// TODO: restructure this code to make it OOP and allow for configuration of multiple actions per
// event as well as the ability to decide whether the event should keep propagating and triggering
// other handlers or not.

document.addEventListener('DOMContentLoaded', () => {
  for (const [eventType, handlers] of Object.entries(HANDLER_MAP)) {
    for (const [selector, handler] of handlers) {
      document.querySelectorAll(selector).forEach((element) => {
        element.addEventListener(eventType, handler);
      });
    }
  }
});
