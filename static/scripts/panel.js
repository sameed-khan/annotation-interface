function populateModal(target, taskData) {
    target.querySelector('form').innerHTML = `
        <div class="columns">
            <div class="column is-half">
                <label class="label">Edit Labels and Keybinds</label> 
                ${taskData.label_keybinds.map(lk => `
                    <div class="field is-flex is-flex-wrap-nowrap mb-1">
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
            </div>
            <div class="column is-half">
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
            </div>
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
        });
    });
});

// Enable add-label button in the new-task modal to add additional labels
document.getElementById('add-label-button').addEventListener('click', function() {
    // Create a new div
    var newDiv = document.createElement('div');

    // Set the innerHTML of the new div
    newDiv.innerHTML = `
        <div class="field is-flex is-flex-wrap-nowrap mb-1">
            <div class="control is-flex-grow-1">
                <input class="input" type="text" placeholder="Enter label">
            </div>
            <div class="control is-flex-grow-0">
                <div class="select">
                    <select>
                        <option>A</option>
                        <option>S</option>
                        <option>D</option>
                        <option>F</option>
                    </select>
                </div>
            </div>
        </div>
    `;

    // Get the add-label-button element
    var button = document.getElementById('add-label-button');

    // Insert the new div before the button
    button.parentNode.insertBefore(newDiv, button);
});

// Darken the background when mouse is hovering over center part of a task display card
document.querySelectorAll('.task-display-card .media-content').forEach(content => {
    cardParent = content.closest('.task-display-card');
    content.addEventListener('mouseenter', () => {
        cardParent.style.filter = 'brightness(90%)';
    });
    content.addEventListener('mouseleave', () => {
        cardParent.style.filter = '';
    });
    content.addEventListener('click', () => {
        let url = new URL(window.location.origin);
        url.pathname = '/label';
        url.searchParams.append('task_id', cardParent.dataset.task_id);
        window.location.href = url.href;
    });
});