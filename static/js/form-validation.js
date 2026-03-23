/* ===== FORM VALIDATION ===== */

import MESSAGES_UK from './locale/form-validation-uk.js';
import MESSAGES_RU from './locale/form-validation-ru.js';
import MESSAGES_EN from './locale/form-validation-en.js';

const LOCALE_MAP = {
    uk: MESSAGES_UK,
    ru: MESSAGES_RU,
    en: MESSAGES_EN,
};

function getMessages() {
    const lang = document.documentElement.lang?.slice(0, 2) || 'uk';
    return LOCALE_MAP[lang] || LOCALE_MAP.uk;
}

document.addEventListener('DOMContentLoaded', () => {
    initFormValidation();
});

function initFormValidation() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });

        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function () {
                validateField(this);
            });

            input.addEventListener('input', function () {
                clearFieldError(this);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');

    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });

    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const isRequired = field.hasAttribute('required');
    const msg = getMessages();

    clearFieldError(field);

    if (isRequired && !value) {
        showFieldError(field, msg.required);
        return false;
    }

    if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showFieldError(field, msg.email);
            return false;
        }
    }

    if (type === 'tel' && value) {
        const phoneRegex = /^[+]?[0-9\s\-(]{9,}[0-9]$/;
        if (!phoneRegex.test(value)) {
            showFieldError(field, msg.phone);
            return false;
        }
    }

    return true;
}

function showFieldError(field, message) {
    const error = document.createElement('span');
    error.className = 'field-error';
    error.textContent = message;

    field.parentNode.appendChild(error);
    field.classList.add('error');
}

function clearFieldError(field) {
    const error = field.parentNode.querySelector('.field-error');
    if (error) {
        error.remove();
    }
    field.classList.remove('error');
}
