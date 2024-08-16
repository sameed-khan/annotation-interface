/**
 * TODO: refactor so that event listeners all listen from shadow root
 * on any input event or keydown event, examine all of the inputs and check for validity
 * rather than relying on a bottom-up approach regulating the individual input elements themselves
 */
import {TemplateResult, html, css} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {BulmaElement} from './bulma-element';

@customElement('label-keybind-input')
export class LabelKeybindInput extends BulmaElement {
  @property({type: Boolean}) isLabelsUnique = true;
  @property({type: Boolean}) isLabelsValid = true;
  @property({type: Boolean}) isKeybindsUnique = true;
  @property({type: Boolean}) isKeybindsValid = true;

  @property({
    type: Array,
    converter: (value: string | null) => {
      if (value === null) {
        console.log('null branch');
        console.log(typeof value);
        console.log(`Received ${value} as lkFields`);
        return [];
      }
      try {
        console.log(`Received ${value} as lkFields`);
        console.log(typeof value);
        return JSON.parse(value.replace(/'/g, '"'));
      } catch (e) {
        console.error('Failed to parse lkFields:', e);
        return [];
      }
    },
  })
  lkFields: Array<{label: string; keybind: string}> = [];
  @state() private _templates: TemplateResult[] = [];
  @state() private _helpTextString: String[] = [];
  @state() private _numLks = 0;

  static styles = [
    BulmaElement.styles,
    css`
      .keybind-input:focus {
        caret-color: transparent;
      }
    `,
  ];

  constructor() {
    super();
    this.addEventListener('keydown', this._isKeybindsUnique);
    this.addEventListener('input', this._isLabelsUnique);
  }

  connectedCallback() {
    super.connectedCallback();
    console.log(this.lkFields);
    this._numLks = this.lkFields.length;
  }

  // Fires off a validate event whenever validation occurs
  protected _dispatchValidateEvent() {
    const isValid =
      this.isLabelsUnique && this.isLabelsValid && this.isKeybindsUnique && this.isKeybindsValid;

    this.dispatchEvent(
      new CustomEvent('validate', {detail: {isValid: isValid}, bubbles: true, composed: true})
    );
  }

  protected _addLabelKeybindInput() {
    // create a new div
    this._numLks++;
    const newLabelKeybindField = html`
      <div class="field is-grouped label-keybind-input-field dynamic-inserted-element mb-1">
        <div class="control is-expanded">
          <input
            name="label-input-${this._numLks}"
            class="input label-input"
            type="text"
            placeholder="Enter label"
            maxlength="20"
            required
            @input=${this._isLabelValid}
          />
        </div>
        <div class="control keybind-control has-text-centered is-expanded">
          <input
            name="keybind-input-${this._numLks}"
            class="input keybind-input"
            autocomplete="off"
            readonly
            onfocus="this.removeAttribute('readonly')"
            @keydown=${this._isKeybindValid}
          />
        </div>
      </div>
    `;
    this._templates = [...this._templates, newLabelKeybindField];
  }

  // closer to keybind element so executed before _isKeybindsUnique
  protected _isKeybindValid(e: Event) {
    e.preventDefault();

    const key = e as KeyboardEvent;
    const inputElement = e.target as HTMLInputElement;

    // Ensure key behavior such that key press shows keybind
    inputElement.value = key.key.toUpperCase();
    if (key.key === ' ') {
      inputElement.value = 'SPACE';
    }

    if (
      key.shiftKey ||
      key.ctrlKey ||
      key.altKey ||
      key.metaKey ||
      key.key === 'z' ||
      key.key === 'Z'
    ) {
      inputElement.classList.add('is-danger');
      this.isKeybindsValid = false;
    } else {
      this.isKeybindsValid = true;
      if (inputElement.classList.contains('is-danger')) {
        inputElement.classList.remove('is-danger');
      }
    }
    this._dispatchValidateEvent();
  }

  protected _isLabelValid(e: Event) {
    const inputElement = e.target as HTMLInputElement;
    const label = inputElement.value;

    const tooLongString = 'Label must be less than 20 characters.';
    const notAlphanumericString = 'Label can include alphanumerics or underscores only.';

    if (label.length > 20) {
      inputElement.classList.add('is-danger');
      this.isLabelsValid = false;
      if (!this._helpTextString.includes(tooLongString)) {
        this._helpTextString = [...this._helpTextString, tooLongString];
      }
    } else {
      if (inputElement.classList.contains('is-danger')) {
        inputElement.classList.remove('is-danger');
      }
      this._helpTextString = this._helpTextString.filter((text) => text !== tooLongString);
      this.isLabelsValid = true;
    }

    if (!/^[a-zA-Z0-9_]*$/.test(label)) {
      inputElement.classList.add('is-danger');
      this.isLabelsValid = false;
      if (!this._helpTextString.includes(notAlphanumericString)) {
        this._helpTextString = [...this._helpTextString, notAlphanumericString];
      }
    } else {
      if (inputElement.classList.contains('is-danger')) {
        inputElement.classList.remove('is-danger');
      }
      this._helpTextString = this._helpTextString.filter((text) => text !== notAlphanumericString);
      this.isLabelsValid = true;
    }
    this._dispatchValidateEvent();
  }

  protected _isKeybindsUnique() {
    console.log('keypress detected');
    let keybindInputs: HTMLInputElement[] = Array.from(
      this.renderRoot.querySelectorAll('.keybind-input') as NodeListOf<HTMLInputElement>
    );
    const slottedKeybindInputs: HTMLInputElement[] = [
      ...(
        (
          this.shadowRoot?.querySelector('slot[name="test"]') as HTMLSlotElement | null
        )?.assignedElements() ?? []
      ).flatMap((el) => {
        const input = el.querySelector('.keybind-input');
        return input instanceof HTMLInputElement ? [input] : [];
      }),
    ];

    slottedKeybindInputs.forEach((input: HTMLInputElement) => keybindInputs.push(input));
    const keybindInputValues = Array.from(keybindInputs).map((input) => input.value);
    const keybindsNotUniqueString = 'Keybinds must be unique.';

    if (new Set(keybindInputValues).size !== keybindInputValues.length) {
      this.isKeybindsUnique = false;
      if (!this._helpTextString.includes(keybindsNotUniqueString)) {
        this._helpTextString = [...this._helpTextString, keybindsNotUniqueString];
      }
      keybindInputs.forEach((input) => {
        input.classList.add('is-danger');
      });
    } else {
      this.isKeybindsUnique = true;
      keybindInputs.forEach((input) => {
        this._helpTextString = this._helpTextString.filter(
          (text) => text !== keybindsNotUniqueString
        );
        if (input.classList.contains('is-danger')) {
          input.classList.remove('is-danger');
        }
      });
    }
    this._dispatchValidateEvent();
  }

  protected _isLabelsUnique() {
    let labelInputs: HTMLInputElement[] = Array.from(
      this.renderRoot.querySelectorAll('.label-input') as NodeListOf<HTMLInputElement>
    );
    const slottedlabelInputs: HTMLInputElement[] = [
      ...(
        (
          this.shadowRoot?.querySelector('slot[name="test"]') as HTMLSlotElement | null
        )?.assignedElements() ?? []
      ).flatMap((el) => {
        const input = el.querySelector('.label-input');
        return input instanceof HTMLInputElement ? [input] : [];
      }),
    ];

    slottedlabelInputs.forEach((input: HTMLInputElement) => labelInputs.push(input));
    const labelInputValues = Array.from(labelInputs).map((input) => input.value);
    const labelsNotUniqueString = 'Labels must be unique.';

    if (new Set(labelInputValues).size !== labelInputValues.length) {
      this.isLabelsUnique = false;
      if (!this._helpTextString.includes(labelsNotUniqueString)) {
        this._helpTextString = [...this._helpTextString, labelsNotUniqueString];
      }
      labelInputs.forEach((input) => {
        input.classList.add('is-danger');
      });
    } else {
      this.isLabelsUnique = true;
      labelInputs.forEach((input) => {
        this._helpTextString = this._helpTextString.filter(
          (text) => text !== labelsNotUniqueString
        );
        if (input.classList.contains('is-danger')) {
          input.classList.remove('is-danger');
        }
      });
    }
    this._dispatchValidateEvent();
  }

  render() {
    return html`
      ${this.lkFields.map(
        (element, index) => html`
          <div class="field is-grouped label-keybind-input-field dynamic-inserted-element mb-1">
            <div class="control is-expanded">
              <input
                name="label-input-${index}"
                class="input label-input"
                type="text"
                value=${element.label.toUpperCase()}
                maxlength="20"
                required
                @input=${this._isLabelValid}
              />
            </div>
            <div class="control keybind-control has-text-centered is-expanded">
              <input
                name="keybind-input-${index}"
                class="input keybind-input"
                value=${element.keybind.toUpperCase()}
                autocomplete="off"
                readonly
                onfocus="this.removeAttribute('readonly')"
                @keydown=${this._isKeybindValid}
              />
            </div>
          </div>
        `
      )}
      ${this._templates}
      <p class="help is-info dynamic-insert-end-boundary">
        ${this._helpTextString.length === 0 ? html`&nbsp;` : this._helpTextString.join(' ')}
      </p>
      <div id="add-label-button-container" class="control">
        <button
          class="add-label-button button is-light is-small"
          type="button"
          @click=${this._addLabelKeybindInput}
        >
          <span class="icon">
            <i class="fa fa-plus"></i>
          </span>
          <span>Add Label</span>
        </button>
      </div>
    `;
  }
}
