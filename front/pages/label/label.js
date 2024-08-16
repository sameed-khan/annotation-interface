import {routes} from '../../shared/scripts/routes.js';
import Panzoom from '@panzoom/panzoom';

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
    if (Number(imageId) < 0 || imageId === null) {
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

class ImageNavigator {
  /**
   * @param {HTMLImageElement} imageElementId: id of the image element to display the image
   * @param {string} taskId: id of the task
   */
  constructor(imageElementId, taskId) {
    this.taskId = taskId;
    this.imageViewer = document.getElementById(imageElementId);
    this.container = this.imageViewer.parentElement;
    this.undoHistory = new AnnotationHistoryBuffer('undoBuffer', 10000);
    this.currentAnnotationId;
    this.panzoom;
  }

  setupPanzoom() {
    this.panzoom = Panzoom(this.imageViewer, {
      maxScale: 5,
      minScale: 0.5,
    });

    this.container.addEventListener('wheel', this.panzoom.zoomWithWheel);
  }

  initializeImage() {
    fetch(`${routes.getNextAnnotation}?task_id=${encodeURIComponent(this.taskId)}`)
      .then((response) => {
        this.currentAnnotationId = response.headers.get('X-Metadata-AnnotationID');
        return response.blob();
      })
      .then((imageBlob) => {
        const imageObjectURL = URL.createObjectURL(imageBlob);
        this.imageViewer.src = imageObjectURL;
        this.imageViewer.onload = () => {
          this.setupPanzoom();
        };
      })
      .catch((error) => console.error('Failed to load initial image:', error));
  }

  loadNextImage(annotationId) {
    let params = new URLSearchParams({
      task_id: encodeURIComponent(this.taskId),
    });
    let updateRoute;

    if (annotationId) {
      params.append('annotation_id', encodeURIComponent(annotationId));
      updateRoute = `${routes.getAnyAnnotation}?${params.toString()}`;
    } else {
      updateRoute = `${routes.getNextAnnotation}?${params.toString()}`;
    }

    fetch(updateRoute)
      .then((response) => {
        this.currentAnnotationId = response.headers.get('X-Metadata-AnnotationID');
        return response.blob();
      })
      .then((imageBlob) => {
        const imageObjectURL = URL.createObjectURL(imageBlob);
        this.imageViewer.src = imageObjectURL;
      })
      .catch((error) => console.error('Failed to load next image:', error));
  }

  async updateAnnotation(label) {
    let params = new URLSearchParams({
      task_id: encodeURIComponent(this.taskId),
      annotation_id: encodeURIComponent(this.currentAnnotationId),
    });
    let updateRoute = `${routes.updateAnnotation}?${params.toString()}`;

    let data = {label: label};
    try {
      let response = await fetch(updateRoute, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      let progressData = await response.json();
      console.log(progressData);
      this.undoHistory.addToBuffer(this.currentAnnotationId);

      return progressData;
    } catch (error) {
      console.error(`Failed annotation update due to ${error}`);
    }
  }

  async undoAnnotation() {
    this.currentAnnotationId = this.undoHistory.popFromBuffer();

    let params = new URLSearchParams({
      task_id: encodeURIComponent(this.taskId),
      annotation_id: encodeURIComponent(this.currentAnnotationId),
    });
    let updateRoute = `${routes.updateAnnotation}?${params.toString()}`;
    let data = {label: ''};

    try {
      let response = await fetch(updateRoute, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      let progressData = await response.json();
      console.log(progressData);
      return progressData;
    } catch (error) {
      console.error(`Failed to undo annotation due to ${error}`);
    }
  }
}

/**
 *
 * @param {integer} labeled : number of labeled annotations in task
 * @param {integer} total : total number of annotations in task
 * @param {float} progress : percent complete
 */
function updateUI(labeled, total, progress) {
  let progbar = document.querySelector('progress');
  let progTextDisplay = document.getElementById('progress-text-display');
  console.log(progress);

  progbar.value = progress;
  progbar.textContent = `${progress}%`;
  progTextDisplay.innerText = `${labeled} / ${total} labeled`;
}

function main() {
  let currentAnnotationId;
  let params = new URLSearchParams(window.location.search);
  const taskId = params.get('task_id');
  let imageNavigator = new ImageNavigator('panzoom-element', taskId);
  let undoHistory = new AnnotationHistoryBuffer('undoBuffer', 10000);

  const labelKeybindMap = new Map();
  let isProcessingKeypress = false;
  let updateProgress;

  document.querySelectorAll('.label-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      updateProgress = await imageNavigator.updateAnnotation(btn.dataset.label);
      updateUI(updateProgress.labeled, updateProgress.total, updateProgress.progress);
      imageNavigator.loadNextImage();

      btn.classList.add('label-button-pressed');
      setTimeout(() => {
        btn.classList.remove('label-button-pressed');
      }, 200);
    });
    labelKeybindMap.set(btn.dataset.keybind.toUpperCase(), btn.dataset.label);
  });

  // Update the keydown listener
  document.addEventListener(
    'keydown',
    async (event) => {
      console.log(
        `keydown event | key: ${event.key} | ctrl: ${event.ctrlKey} | isProcessingKeypress: ${isProcessingKeypress}`
      );

      // Prevent modifier keys from triggering keypress
      if (isProcessingKeypress) {
        return;
      }

      if (event.key.length === 1) {
        isProcessingKeypress = true;
      }

      if (
        labelKeybindMap.has(event.key.toUpperCase) ||
        event.ctrlKey ||
        event.key == 'z' ||
        event.key == 'Z'
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }

      if (labelKeybindMap.has(event.key.toUpperCase())) {
        let label = labelKeybindMap.get(event.key.toUpperCase());
        let updatePromise = imageNavigator.updateAnnotation(label);
        updatePromise.then((updateProgress) => {
          updateUI(updateProgress.labeled, updateProgress.total, updateProgress.progress);
          imageNavigator.loadNextImage();
        });

        document
          .getElementById(`btn-${event.key.toUpperCase()}`)
          .classList.add('label-button-pressed');
        setTimeout(() => {
          document
            .getElementById(`btn-${event.key.toUpperCase()}`)
            .classList.remove('label-button-pressed');
        }, 200);
      } else if (event.ctrlKey && event.key === 'z') {
        console.log('Undo event fired!');
        console.log(imageNavigator.currentAnnotationId);
        if (imageNavigator.undoHistory.isEmpty()) {
          alert('All previous labels have been undone or there are no labels to undo.');
          return;
        }

        let updatePromise = imageNavigator.undoAnnotation();
        updatePromise.then((updateProgress) => {
          updateUI(updateProgress.labeled, updateProgress.total, updateProgress.progress);
          imageNavigator.loadNextImage(imageNavigator.currentAnnotationId);
        });
      }
    },
    {capture: true}
  );

  document.addEventListener(
    'keyup',
    (event) => {
      console.log('keyup event', event.key, isProcessingKeypress);
      isProcessingKeypress = false;
    },
    {capture: true}
  );

  // Set up image display
  imageNavigator.initializeImage();
  // TODO: fix this jank -- should not
  // rely on imageNavigator to get id
}

document.addEventListener('DOMContentLoaded', () => {
  main();
});
