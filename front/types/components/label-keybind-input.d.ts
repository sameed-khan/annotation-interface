import { TemplateResult } from 'lit';
import { BulmaElement } from './bulma-element';
export declare class LabelKeybindInput extends BulmaElement {
    isValid: boolean;
    lkFields: Array<{
        label: string;
        keybind: string;
    }>;
    private _templates;
    private _helpTextString;
    private _numLks;
    static styles: import("lit").CSSResultGroup[];
    constructor();
    connectedCallback(): void;
    protected _addLabelKeybindInput(): void;
    protected _isKeybindValid(e: Event): void;
    protected _isLabelValid(e: Event): void;
    protected _isKeybindsUnique(): void;
    protected _isLabelsUnique(): void;
    render(): TemplateResult<1>;
}
