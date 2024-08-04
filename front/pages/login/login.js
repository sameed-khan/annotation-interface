import { routes } from './routes.js';


document.addEventListener('DOMContentLoaded', () => {
    // If there was an incorrect login
    const loginFailed = localStorage.getItem('loginFailed');
    if (loginFailed) {
        localStorage.removeItem('loginFailed');
        const loginFailedNotif = document.getElementById('login-failed-notification');
        loginFailedNotif.classList.remove('is-hidden');
    }
    // Functions to open and close a modal
    function openModal(el) {
        el.classList.add('is-active');
    }

    function closeModal(el) {
        el.classList.remove('is-active');
    }

    function closeAllModals() {
        (document.querySelectorAll('.modal') || []).forEach((modal) => {
            closeModal(modal);
        });
    }

    // Add a click event on buttons to open a specific modal
    (document.querySelectorAll('.js-modal-trigger') || []).forEach((trigger) => {
        const modal = trigger.dataset.target;
        const target = document.getElementById(modal);

        trigger.addEventListener('click', () => {
            openModal(target);
        });
    });

    // Add a click event on various child elements to close the parent modal
    (document.querySelectorAll('.modal-background, .modal-close, .cancel-close, .modal-card-head, .delete, .modal-card-foot') || []).forEach((close) => {
        const target = close.closest('.modal');

        close.addEventListener('click', () => {
            closeModal(target);
        });
    });

    // Add a keyboard event to close all modals
    document.addEventListener('keydown', (event) => {
        if(event.key === "Escape") {
            closeAllModals();
        }
    });
});

const usernameInput = document.getElementById('username-input');
const availableHelpText = document.getElementById('register-form-available-helptext');
const unavailableHelpText = document.getElementById('register-form-unavailable-helptext');

const passwordInput = document.getElementById('password-input');
const verifyPasswordInput = document.getElementById('verify-password-input');
const nomatchHelpText = document.getElementById('register-form-nomatch-helptext');
const newUserSubmitButton = document.getElementById('new-user-submit-button')

usernameInput.addEventListener('input', function() {
    if (usernameInput.value.length > 0) {
        availableHelpText.classList.remove('is-hidden');
        fetch(`${routes.checkUsername}?request_username=${encodeURIComponent(usernameInput.value)}`)
        .then(response => response.json())
        .then(data => {
            if (data.available) {
                availableHelpText.classList.remove('is-hidden');
                unavailableHelpText.classList.add('is-hidden');
                newUserSubmitButton.disabled = false;
            } else {
                availableHelpText.classList.add('is-hidden');
                unavailableHelpText.classList.remove('is-hidden');
                newUserSubmitButton.disabled = true;
            }
        });
    } else {
        availableHelpText.classList.add('is-hidden');
        unavailableHelpText.classList.add('is-hidden');
    }
});

verifyPasswordInput.addEventListener('input', function() {
    if (verifyPasswordInput.value !== passwordInput.value) {
        nomatchHelpText.classList.remove('is-hidden');
        newUserSubmitButton.disabled = true;
    } else {
        nomatchHelpText.classList.add('is-hidden');
        newUserSubmitButton.disabled = false;
    }
});

var form = document.getElementById('login-form');
form.addEventListener('submit', function(event) {
    event.preventDefault();
    fetch(routes.loginUser, {
        method: 'POST',
        body: JSON.stringify(Object.fromEntries(new FormData(form))),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            switch (response.status) {
                case 401:
                case 403:
                    document.getElementById('login-failed-notification').classList.remove('is-hidden');
                    setTimeout(() => {
                        document.getElementById('login-failed-notification').classList.add('is-hidden');
                    }, 5000);
                    break;
                case 404:
                    alert("This server has not been set up to handle logins.");
                    break;
                case 500:
                    alert("Internal server error. Please contact the developer.");
                    console.log(response);
                default:
                    alert("Unhandled error. Please contact the developer.");
                    console.log(response);
            }
            throw new Error('Error:', response); 
        }
        return response.json();
    })
    .then(data => {
        window.location.href = data.url;
    })
    .catch(error => {
        console.error('Error:', error);
    })
});