export class FormValidationManager {
    constructor(uiValidUpdateFunc, uiInvalidUpdateFunc, helpTextElement, submitButton, ...formValidationControls) {
    /**
     * @param {Function} uiValidUpdateFunc The function to call when the form is valid
     * @param {Function} uiInvalidUpdateFunc The function to call when the form is invalid
     * @param {HTMLElement} helpTextElement The element to display the help text
     * @param {HTMlElement} submitButton The submit button for the form
     * @param {Array[FormValidationControl]} formValidationControls An array of FormValidationControl objects
    */
        this._uiValidUpdateFunc = uiValidUpdateFunc;
        this._uiInvalidUpdateFunc = uiInvalidUpdateFunc;
        this._helpTextElement = helpTextElement;
        this._formValidationControls = formValidationControls;
        this._submitButton = submitButton;

        this._helperTextString = '';
        this._formElement = this._formValidationControls[0].formElement; // All form elements should be the same element
    }

    uiUpdateInvalid() {
        this._uiInvalidUpdateFunc(this._formElement);
        this._submitButton.disabled = true;
    }

    uiUpdateValid() {
        this._uiValidUpdateFunc(this._formElement);
        this._submitButton.disabled = false;
    }

    apply_validation() {
        let allValid = this._formValidationControls.every(control => control.validate());
        if (allValid) {
            this.uiUpdateValid();
            this._helpTextElement.textContent = '';
            return;
        }

        this.uiUpdateInvalid();

        // Construct the helper text string
        this._formValidationControls.forEach(control => {
            if (!control.validate()) {
                this._helperTextString += control._helperText + ' ';
            }
        })
        this._helpTextElement.textContent = this._helperTextString;
    }
}
export class FormValidationControl {
    constructor(formElement, formValidator, helperText) {
        /**
         * @param {HTMLElement | Array[HTMLElement]} formElement The form element(s) to validate
         * @param {Function} formValidator The function to validate the form. Only accepts one string argument. Only returns a boolean.
         * @param {string} helperText The text to display when validation fails. Should be no more than 5 words and declarative ( e.g. "Only alphanumeric characters allowed.")
         */

        this.formElement = formElement;
        this._formValidator = formValidator;
        this._helperText = helperText;
    }

    validate() {
        let formValue = this.formElement.value;
        let isValid = this._formValidator(formValue);
        return isValid;
    }
}

export function onlyAlphanumericSpacesHyphens(value) {
    return /^[a-zA-Z0-9\s-]*$/.test(value);
}

export function onlyAlphaNumeric(value) {
    return /^[a-zA-Z0-9]*$/.test(value);
}

export function notUndoKey(value) {
    return value.toLowerCase() !== 'z';
}

export function onlySingleCharacter(value) {
    return value.length === 1;
}

export function allItemsUnique(otherValues, checkValue){
    if ((checkValue.length === 0) || (otherValues.every(v => v === ''))) { return true; }

    let processedValue = otherValues.map(v => v.toLowerCase().trim().replace(/\s/g, ''));
    let processedCheck = checkValue.toLowerCase().trim().replace(/\s/g, '');
    return processedValue.filter(v => v === processedCheck).length <= 1;
}

// UI Update Functions
export function bulmaSetDanger(value) {
    value.classList.add('is-danger');
}

export function bulmaRemoveDanger(value) {
    value.classList.remove('is-danger');
}

export function partial(func, ...args) {
    return function() {
        return func(...args, ...arguments);
    }
}

// Escape odd numbered sequences of backslashes to handle Windows path
const RE_ODD_BACKSLASH_SEQUENCE = /(?<!\\)(\\{1}(?:\\{2})*)(?!\\)/g;

export function escapeBackslashes(str) {
    return str.replace(RE_ODD_BACKSLASH_SEQUENCE, '$1\\');
}