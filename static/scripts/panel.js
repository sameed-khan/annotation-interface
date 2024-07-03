import { routes } from './routes.js';
import { 
    FormValidationManager, FormValidationControl, onlyAlphaNumeric, 
    onlyAlphanumericSpacesHyphens, onlySingleCharacter, allItemsUnique, bulmaRemoveDanger,
    bulmaSetDanger, partial, escapeBackslashes, notUndoKey
 } from './validation.js';


function populateModal(target, taskData) {
    target.querySelector('form').innerHTML = `
        <div class="columns">
            <fieldset name="label-keybind-input-form-group" class="column is-half">
                <label class="label">Edit Labels and Keybinds</label> 
                ${taskData.label_keybinds.map(lk => `
                    <div class="field label-keybind-input-field is-flex is-flex-wrap-nowrap mb-1">
                        <div class="control is-flex-grow-1">
                            <input class="input" type="text" value="${lk.label}" required>
                        </div>
                        <div class="control is-flex-grow-0">
                            <div class="select">
                                <select>
                                    ${['A', 'S', 'D', 'F', 'J', 'K', 'L', ';'].map(key => 
                                        `<option ${key === lk.keybind ? 'selected' : ''}>${key}</option>`
                                    ).join('')}
                                </select>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </fieldset>
            <fieldset name="file-select-input-form-group" class="column is-half">
                <label class="label">Select Images to Include</label>
                ${taskData.files.map(file => `
                    <div class="field">
                        <div class="control task-file-select-control">
                            <label class="b-checkbox checkbox task-file-select">
                                <input type="checkbox" ${file.included ? 'checked' : ''}>
                                <span class="check is-info"></span>
                                <span class="control-label">${file.name}</span>
                            </label>
                        </div>
                    </div>
                `).join('')}
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
     *                                       =>     lks: [
     *  [label1, keybind1],                                 {label: 'label1', keybind: 'keybind1'}, 
     *  [label2, keybind2],                                 {label: 'label2', keybind: 'keybind2'}, 
     *  ...]                                            ...]
     *                                          } 
     */

    let taskData = {
        root: null,
        lks: [],
    }

    formData.forEach((key, value) => {
        if (key.startsWith('label-input-')) {
            let lkIndex = key.split('-')[2];
            let lk = taskData.lks[lkIndex] || {};
            lk.label = value;
            taskData.lks[lkIndex] = lk;
        } else if (key.startsWith('keybind-input-')) {
            let lkIndex = key.split('-')[2];
            let lk = taskData.lks[lkIndex] || {};
            lk.keybind = value;
            taskData.lks[lkIndex] = lk;
        } else if (key === 'root-folder-input') {
            let backSlashEscaped = escapeBackslashes(value);
            taskData.root = encodeURIComponent(backSlashEscaped);
        } else if (key === 'task-title-input') {
            taskData.title = value;
        } else {
            throw new Error('Invalid form data key found: ' + key);
        }
    });

    return taskData;
}
document.addEventListener('DOMContentLoaded', () => {
    // Enable opening modals for all buttons
    (document.querySelectorAll('.js-modal-trigger') || []).forEach((trigger) => {
        const modal = trigger.dataset.target;
        const target = document.getElementById(modal);

        trigger.addEventListener('click', () => {
            const taskId = trigger.dataset.task_id;
            fetch(`/panel/get_task_keybinds?task_id=${encodeURIComponent(taskId)}`)
            .then(response => response.json())
            .then(data => {
                populateModal(target, data)
            })
            target.showModal();
        });
    });

    // Close any modal by clicking outside in the background
    (document.querySelectorAll('dialog') || []).forEach((modal) => {
        modal.addEventListener('click', function(close) {
            var rect = modal.getBoundingClientRect();
            var isInModal=(rect.top <= close.clientY && close.clientY <= rect.top + rect.height
                && rect.left <= close.clientX && close.clientX <= rect.left + rect.width);
            if (!isInModal) {
                modal.close();
            }
        });
    });

    (document.querySelectorAll('.cancel-close') || []).forEach((close) => {
        const target = close.closest('dialog');

        close.addEventListener('click', () => {
            target.close();
            target.querySelectorAll('.dynamic-inserted-element').forEach(element => { element.remove() })
        });
    });
});

// Handle add-label button in the new-task modal
var lkSelectControls = 2; // the html template always starts with 2 label-keybind select fields
// Enable add-label button in the new-task modal to add additional labels
document.getElementById('add-label-button').addEventListener('click', function() {
    // Create a new div
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

    // Get the last instance of the above type of element and insert as next sibling
    let endBoundaryElement = document.querySelector('.dynamic-insert-end-boundary');
    let parentFieldset = document.getElementById('task-creation-lk-fieldset');
    parentFieldset.insertBefore(newDiv, endBoundaryElement)

    // Now that the element is inserted, we can safely change the outerHTML
    newDiv.outerHTML = newElementHTML;

    // Increment the lkSelectControls counter
    lkSelectControls++;
});

// Darken the background when mouse is hovering over center part of a task display card
// document.querySelectorAll('.task-display-card .media-content').forEach(content => {
//     cardParent = content.closest('.task-display-card');
//     content.addEventListener('mouseenter', () => {
//         cardParent.style.filter = 'brightness(90%)';
//     });
//     content.addEventListener('mouseleave', () => {
//         cardParent.style.filter = '';
//     });
//     content.addEventListener('click', () => {
//         let url = new URL(window.location.origin);
//         url.pathname = '/label';
//         url.searchParams.append('task_id', cardParent.dataset.task_id);
//         window.location.href = url.href;
//     });
// });

// Handle form validatino for root folder input field
document.getElementById('root-folder-input').addEventListener('input', () => {
    let rootFolderInput = document.getElementById('root-folder-input');
    let submitButton = document.getElementById('task-creation-submit-button');
    let invalidRootFolderHelpText = document.getElementById('root-folder-help-text-danger');
    let validRootFolderHelpText = document.getElementById('root-folder-help-text-info');

    fetch(`${routes.checkPath}?path=${encodeURIComponent(rootFolderInput.value)}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(response.statusText);
        }
        return response.json();
    })
    .then(data => {
        validRootFolderHelpText.textContent = `Found ${data.file_count} files to annotate`
        validRootFolderHelpText.classList.remove('is-hidden');
        invalidRootFolderHelpText.classList.add('is-hidden');
        submitButton.disabled = false;
    })
    .catch((error) => {
        invalidRootFolderHelpText.textContent = error.message;
        invalidRootFolderHelpText.classList.remove('is-hidden');
        validRootFolderHelpText.classList.add('is-hidden');
        submitButton.disabled = true;
    })
})

// Handle form validation for new-task modal label inputs
document.getElementById('task-creation-form').querySelectorAll('input.label-input').forEach(inputElement => {
    inputElement.addEventListener('input', () => {
        let submitButton = document.getElementById('task-creation-submit-button');
        let labelAlphaNumericSpaceHyphenValidation = new FormValidationControl(
            inputElement,
            onlyAlphanumericSpacesHyphens,
            'Only alphanumeric characters, spaces, and hyphens allowed.',
        ); 

        let labelLessThan20CharsValidation = new FormValidationControl(
            inputElement,
            (value) => value.length <= 20,
        )

        let otherLabels = [
            ...inputElement.closest('fieldset').querySelectorAll('input.label-input')
        ].map(input => input.value);

        let labelsUniqueValidation = new FormValidationControl(
            inputElement,
            partial(allItemsUnique, otherLabels),
            'Labels are case and space insensitive and must be unique.',
        );

        let labelValidationManager = new FormValidationManager(
            bulmaRemoveDanger,
            bulmaSetDanger,
            inputElement.closest('fieldset').querySelector('p.help'),
            submitButton,
            labelAlphaNumericSpaceHyphenValidation,
            labelsUniqueValidation,
        );

        labelValidationManager.apply_validation();
            
    });
})

// Capture KEYPRESS event for keybind inputs and insert that key into the input field
document.getElementById('task-creation-form').querySelectorAll('input.keybind-input').forEach(inputElement => {
    inputElement.addEventListener('keydown', (event) => {
        event.preventDefault();
        inputElement.value = event.key;
        let helpTextElement = inputElement.closest('fieldset').querySelector('p.help');
        let submitButton = document.getElementById('task-creation-submit-button');

        let otherKeybinds = [
            ...inputElement.closest('fieldset').querySelectorAll('input.keybind-input')
        ].map(input => input.value);

        let keybindsUniqueValidation = new FormValidationControl(
            inputElement,
            partial(allItemsUnique, otherKeybinds),
            'Keybinds are case-insensitive and must be unique.',
        )

        let notUndoKeyValidation = new FormValidationControl(
            inputElement,
            notUndoKey,
            '"Z" and "z" are reserved for undo. Please choose another key.'
        )

        let labelValidationManager = new FormValidationManager(
            bulmaRemoveDanger,
            bulmaSetDanger,
            helpTextElement,
            submitButton,
            keybindsUniqueValidation,
            notUndoKeyValidation
        );

        labelValidationManager.apply_validation();

        if (event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) {
            console.log('modifier key detected');
            inputElement.classList.add('is-danger');
            helpTextElement.textContent = 'Keybind must not include modifier keys (Shift, Ctrl, Alt, or Meta).';
        } 
    });
})

document.getElementById('task-creation-form').addEventListener('submit', function(event) {
    event.preventDefault();
    let formData = new FormData(event.target);
    let taskData = generateRequestFromTaskCreationForm(formData);
    fetch(routes.createTask, {
        method: 'POST',
        body: JSON.stringify(taskData),
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(response.statusText);
        }
        return response.json();
    })
    .then(() => {
        // Reload the page to show the new task
        window.location.reload();
    })
    .then((error) => {
        console.error(error);
        event.target.reset();
        alert('An error occurred while creating the task.');
    })
});

// Handle switching of tabs on user click - task manage modal trigger
document.querySelectorAll("a.task-manage-modal-trigger").forEach((triggerElement) => {
    triggerElement.addEventListener("click", (event) => {
        event.preventDefault();
        let targetModal = document.getElementById(triggerElement.dataset.target);
        document.querySelectorAll('li.task-manage-tab').forEach(tab=> { tab.classList.remove('is-active') });
        document.querySelectorAll('form.new-task-form').forEach(form => {
            form.reset();
            form.querySelectorAll('.dynamic-inserted-element').forEach(element => { element.remove() });
            form.classList.add('is-hidden');
        });

        triggerElement.closest('li.task-manage-tab').classList.add('is-active');
        targetModal.classList.remove('is-hidden');

    })
});