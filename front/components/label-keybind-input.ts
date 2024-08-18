/**
 * TODO: refactor so that event listeners all listen from shadow root
 * on any input event or keydown event, examine all of the inputs and check for validity
 * rather than relying on a bottom-up approach regulating the individual input elements themselves
 */
import {PropertyValues, css, html} from 'lit';
import {ifDefined} from 'lit/directives/if-defined.js';
import {customElement, property, state} from 'lit/decorators.js';
import {BulmaElement} from './bulma-element';
import {sortByKeyboardLayout, KEYBOARD_LAYOUT} from '../shared/scripts/utilities';

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
  lkFields: Array<{label: string | null; keybind: string | null; id: string | null}> = [];
  @state() private _helpTextString: String[] = [];

  static styles = [
    BulmaElement.styles,
    css`
      .keybind-input:focus {
        caret-color: transparent;
      }
      .delete-label-keybind-field-button {
        margin-right: -0.5rem;
      }
    `,
  ];

  static formAssociated = true;
  public internals: ElementInternals | undefined;

  constructor() {
    super();
    this.internals = this.attachInternals();
    this.addEventListener('keydown', (event) => {
      this._updatePropertyFromEvent(event);
      this._isKeybindsUnique();
      this._updateFormData();
    });
    this.addEventListener('input', (event) => {
      this._updatePropertyFromEvent(event);
      this._isLabelsUnique();
      this._updateFormData();
    });
  }

  connectedCallback() {
    super.connectedCallback();
    this.lkFields.sort((a, b) => sortByKeyboardLayout(a.keybind, b.keybind));
  }

  firstUpdated(changedProperties: PropertyValues) {
    super.firstUpdated(changedProperties);
    this._updateFormData();
  }

  protected _updateFormData() {
    // TODO: can we just return lkFields?
    // have to figure out how the backend processes null value for lk_id
    // to figure that out -- if we pass in null how does that get passed onto the backend?
    const labelKeybindPairs = this.lkFields.map((lkField) => {
      return lkField.id
        ? {
            lk_id: lkField.id,
            label: lkField.label,
            keybind: lkField.keybind,
          }
        : {
            label: lkField.label,
            keybind: lkField.keybind,
          };
    });
    console.log(`Updating form data with ${JSON.stringify(labelKeybindPairs)}`);
    this.internals?.setFormValue(JSON.stringify(labelKeybindPairs));
  }

  // Fires off a validate event whenever validation occurs
  protected _dispatchValidateEvent() {
    const isValid =
      this.isLabelsUnique && this.isLabelsValid && this.isKeybindsUnique && this.isKeybindsValid;

    this.dispatchEvent(
      new CustomEvent('validate', {detail: {isValid: isValid}, bubbles: true, composed: true})
    );
  }

  protected _updatePropertyFromEvent(event: Event) {
    // update lkFields with the new values
    // this function updates regardless of validation status
    const parentField = <HTMLDivElement>(
      (<Element>event.composedPath()[0])!.closest('div.label-keybind-input-field')
    );
    console.log(parentField);
    const lkFieldsIndex = Number(parentField.dataset.index);
    const label = (<HTMLInputElement>parentField.querySelector('.label-input'))!.value;
    const keybind = (<HTMLInputElement>parentField.querySelector('.keybind-input'))!.value;

    // we want the assumption that _addLabelKeybindInput will always be called before this
    // and will have created the member in lkFields array that we will now modify
    this.lkFields[lkFieldsIndex] = {label: label, keybind: keybind, id: null};
  }

  protected _addLabelKeybindInput() {
    // since redefining lkFields, this will trigger a re-render
    this.lkFields = [...this.lkFields, {label: null, keybind: null, id: null}];
  }

  protected _deleteLabelKeybindInput(e: Event) {
    const button = <HTMLButtonElement>e.currentTarget;
    const parent = <HTMLDivElement>button.closest('div.label-keybind-input-field');

    const lkFieldsIndex = Number(parent.dataset.index);
    this.lkFields = this.lkFields.filter((_, index) => index !== lkFieldsIndex);
    this._updateFormData(); // update here because there may have been input in the field
  }

  // closer to keybind element so executed before _isKeybindsUnique
  protected _isKeybindValid(e: Event) {
    e.preventDefault();

    const key = <KeyboardEvent>e;
    const inputElement = <HTMLInputElement>e.target;
    const invalidKeybindString = 'Keybind must be alphabetical (except z), semicolon, or space.';

    let keyValue = key.key.toUpperCase();
    if (keyValue === ' ') {
      keyValue = 'SPACE';
    }
    inputElement.value = keyValue;

    if (!KEYBOARD_LAYOUT.includes(keyValue.toLowerCase())) {
      inputElement.classList.add('is-danger');
      this.isKeybindsValid = false;
      if (!this._helpTextString.includes(invalidKeybindString)) {
        this._helpTextString = [...this._helpTextString, invalidKeybindString];
      }
    } else {
      this.isKeybindsValid = true;
      this._helpTextString = this._helpTextString.filter((text) => text !== invalidKeybindString);
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
    const notAlphanumericString = 'Only alphanumeric characters, spaces, and hyphens allowed.';

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

    if (!/^[a-zA-Z0-9\-\s]*$/.test(label)) {
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
          <div class="field is-grouped label-keybind-input-field mb-1" data-index="${index}">
            <button
              class="button delete-label-keybind-field-button is-small is-outlined is-danger is-light"
              @click=${this._deleteLabelKeybindInput}
            >
              <span class="icon">
                <i class="fa fa-x"></i>
              </span>
            </button>
            <div class="control is-expanded">
              <input
                name="label-input-${index}"
                class="input label-input"
                type="text"
                value=${element.label?.toUpperCase() ? element.label.toUpperCase() : ''}
                data-db_id=${ifDefined(element.id)}
                maxlength="20"
                required
                @input=${this._isLabelValid}
              />
            </div>
            <div class="control keybind-control has-text-centered is-expanded">
              <input
                name="keybind-input-${index}"
                class="input keybind-input"
                value=${element.keybind?.toUpperCase() ? element.keybind.toUpperCase() : ''}
                autocomplete="off"
                readonly
                onfocus="this.removeAttribute('readonly')"
                required
                @keydown=${this._isKeybindValid}
              />
            </div>
          </div>
        `
      )}
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
