/**
 * Survey modal – open/close/submit.
 * Reads CSRF token from <meta name="csrf-token">.
 */

const modal   = document.getElementById('surveyModal');
const form    = document.getElementById('surveyForm');
const msgEl   = document.getElementById('surveyFormMsg');

if (!modal) throw new Error('surveyModal element not found');

const openModal = () => {
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    modal.querySelector('.survey-modal__dialog')?.setAttribute('tabindex', '-1');
    modal.querySelector('.survey-modal__dialog')?.focus();
};

const closeModal = () => {
    modal.hidden = true;
    document.body.style.overflow = '';
};

const showMsg = (text, type) => {
    if (!msgEl) return;
    msgEl.hidden = false;
    msgEl.className = `sf-message sf-message--${type}`;
    msgEl.textContent = text;
    msgEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
};

const hideMsg = () => {
    if (!msgEl) return;
    msgEl.hidden = true;
    msgEl.className = 'sf-message';
    msgEl.textContent = '';
};

/* ── Open triggers ── */
document.querySelectorAll('[data-survey-open]').forEach(btn => {
    btn.addEventListener('click', openModal);
});

/* ── Close triggers (backdrop + ×) ── */
modal.addEventListener('click', e => {
    if (e.target.closest('[data-survey-close]')) closeModal();
});

/* ── ESC key ── */
document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
});

/* ── Form submit ── */
form?.addEventListener('submit', async e => {
    e.preventDefault();
    hideMsg();

    const submitBtn = form.querySelector('[type="submit"]');
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ?? '';

    submitBtn.disabled = true;
    const origText = submitBtn.textContent;
    submitBtn.textContent = 'Відправляємо…';

    try {
        const body = new FormData(form);
        const res  = await fetch(form.action, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            body,
        });

        const data = await res.json();

        if (data.success) {
            showMsg(data.message, 'success');
            form.reset();
            setTimeout(closeModal, 3500);
        } else {
            showMsg(data.message ?? 'Виникла помилка. Спробуйте пізніше.', 'error');
        }
    } catch {
        showMsg('Мережева помилка. Перевірте підключення та спробуйте знову.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = origText;
    }
});
