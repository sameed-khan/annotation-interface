import { routes } from './routes.js';


class ImageNavigator {
    constructor(viewerId, taskId) {
        this.viewer = OpenSeadragon({
            id: viewerId,
            prefixUrl: "/static/assets/openseadragon/images/",
            showNavigationControl: true,
            showFullPageControl: true,
        });
        this.taskId = taskId;
    }

    loadImage(imageId) {
        return new Promise((resolve, reject) => {
            this.viewer.open({
                tileSource: {
                    type: 'image',
                    url: `/label/get_image?annotation_id=${encodeURIComponent(imageId)}`,
                    buildPyramid: false
                },
                success: () => resolve(imageId),
                error: (error) => {
                    console.error('Failed to load image:', error);
                    reject(error);
                }
            });
        });
    }
}

class AnnotationHistoryBuffer {
    constructor(bufferKey, bufferLimit) {
        this.bufferKey = bufferKey;
        this.bufferLimit = bufferLimit;
        if (!localStorage.getItem(this.bufferKey)) {
            localStorage.setItem(this.bufferKey, JSON.stringify([]));
        }
    }

    isEmpty() {
        return JSON.parse(localStorage.getItem(this.bufferKey)).length === 0;
    }

    addToBuffer(imageId) {
        if (imageId === 0 || imageId === null) {
            return;
        }
        let buffer = JSON.parse(localStorage.getItem(this.bufferKey));
        buffer.push(imageId);
        if (buffer.length > this.bufferLimit) {
            buffer.shift();
        }
        localStorage.setItem(this.bufferKey, JSON.stringify(buffer));
    }

    popFromBuffer() {
        let buffer = JSON.parse(localStorage.getItem(this.bufferKey));
        if (buffer.length > 0) {
            let retId = buffer.pop();
            localStorage.setItem(this.bufferKey, JSON.stringify(buffer));
            return retId;
        }
        return 0;
    }
}

function updateServer(path_suffix, task_uuid, image_id, label) {
    let updateRoute = `/label/${path_suffix}`;
    let data = { task_uuid: task_uuid, annotation_id: image_id, label: label };
    return fetch(updateRoute, {  // Return the Promise
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => { 
        console.log(data);
        let progbar = document.querySelector("progress");
        progbar.value = data.progress_percent;
        progbar.textContent = `${data.progress_percent}%`;

        document.getElementById("progress-text-display").innerText = `${data.labeled} / ${data.total} labeled`;

        return data.next_id; 
    });
}

document.addEventListener('DOMContentLoaded', () => {
    var currentImageId;
    const taskID = document.body.dataset.task_uuid
    const labelKeybindMap = new Map();
    var imageNavigator = new ImageNavigator('osd-viewer', taskID);
    var undoHistory = new AnnotationHistoryBuffer('undoBuffer', 10000);
    var isProcessingKeypress = false;

    console.log(taskID);

    // Get initial image that has not been labeled yet
    fetch( `/label/get_next_annotation?task_uuid=${encodeURIComponent(taskID)}` )
    .then(response => response.json())
    .then(data => {
        currentImageId = data.next_id;
        imageNavigator.loadImage(currentImageId);
    })
    .catch(error => console.error('Failed to load initial image:', error));

    // Update the click listeners
    document.querySelectorAll('.label-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            undoHistory.addToBuffer(currentImageId);
            console.log(currentImageId);
            updateServer('update_annotation', taskID, currentImageId, btn.dataset.label).then((nextId) => { 
                currentImageId = nextId; 
                console.log("Current image ID after update: ", currentImageId);
                imageNavigator.loadImage(currentImageId)
            })
            .catch(error => console.error('Failed to load next image:', error));

            btn.classList.add('label-button-pressed');
            setTimeout(() => {
                btn.classList.remove('label-button-pressed');
            }, 200);
        })
        labelKeybindMap.set(btn.dataset.keybind, btn.dataset.label);
    });

    // Update the keydown listener
    document.addEventListener('keydown', (event) => {
        console.log(`keydown event | key: ${event.key} | ctrl: ${event.ctrlKey} | isProcessingKeypress: ${isProcessingKeypress}`)

        // Prevent modifier keys from triggering keypress
        if(isProcessingKeypress) {
            return;
        }

        if (event.key.length === 1) {
            isProcessingKeypress = true;
        }

        event.preventDefault();
        event.stopImmediatePropagation();
        if (labelKeybindMap.has(event.key.toUpperCase())) {
            undoHistory.addToBuffer(currentImageId);
            updateServer('update_annotation', taskID, currentImageId, labelKeybindMap.get(event.key.toUpperCase()))
                .then((nextId) => { 
                    currentImageId = nextId;
                    return imageNavigator.loadImage(currentImageId);
                })
                .catch(error => console.error('Failed to load next image:', error));

            document.getElementById(`btn-${event.key.toUpperCase()}`).classList.add('label-button-pressed');
            setTimeout(() => {
                document.getElementById(`btn-${event.key.toUpperCase()}`).classList.remove('label-button-pressed');
            }, 200);
        } else if (event.ctrlKey && event.key === 'z') {
            console.log(currentImageId);
            if (undoHistory.isEmpty()) {
                alert('All previous labels have been undone or there are no labels to undo.');
                return;
            }
            currentImageId = undoHistory.popFromBuffer();
            updateServer('undo_annotation', taskID, currentImageId, "")
                .then(() => { 
                    return imageNavigator.loadImage(currentImageId);
                })
                .catch(error => console.error('Failed to load previous image:', error));
        }
    }, { capture: true });

    document.addEventListener('keyup', (event) => {
        console.log("keyup event", event.key, isProcessingKeypress)
        isProcessingKeypress = false;
    }, { capture: true })
});