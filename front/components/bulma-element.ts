import {LitElement, CSSResultGroup} from 'lit';
import {bulmaStyles} from './bulmaStyles';
import {faAllStyle} from './faAll';

export class BulmaElement extends LitElement {
  static styles: CSSResultGroup = [bulmaStyles, faAllStyle];

  constructor() {
    super();
    this.injectFont();
  }

  connectedCallback() {
    super.connectedCallback();
  }

  injectFont() {
    if (!document.querySelector('#font-awesome-style')) {
      const style = document.createElement('style');
      style.id = 'font-awesome-style';
      style.textContent = `
            @font-face {
                font-family: 'Font Awesome 6 Free';
                font-style: normal;
                font-weight: 400;
                font-display: block;
                src: url("/static/fontawesome-6-web/webfonts/fa-regular-400.woff2") format("woff2"),
                      url("/static/fontawesome-6-web/webfonts/fa-regular-400.ttf") format("truetype");
            }

            .far,
            .fa-regular {
                font-weight: 400;
            }

            :root, :host {
                --fa-style-family-classic: 'Font Awesome 6 Free';
                --fa-font-solid: normal 900 1em/1 'Font Awesome 6 Free';
            }

            @font-face {
                font-family: 'Font Awesome 6 Free';
                font-style: normal;
                font-weight: 900;
                font-display: block;
                src: url("/static/fontawesome-6-web/webfonts/fa-solid-900.woff2") format("woff2"),
                      url("/static/fontawesome-6-web/webfonts/fa-solid-900.ttf") format("truetype");
            }
          `;
      document.head.appendChild(style);
    }
  }
}

customElements.define('bulma-element', BulmaElement);
