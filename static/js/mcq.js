/**
 * mcq.js — MCQ quiz controller.
 * Handles: question navigation, timer, answer selection, progress bar,
 * dot navigation, and auto-submit on timer expiry.
 */

let currentQuestion = 0;
let totalQuestions  = 0;
let timerInterval   = null;
let secondsLeft     = 20 * 60;  // 20 minutes
const answeredMap   = {};        // { questionIndex: selectedOption }

/**
 * Entry point — called from the template after DOM is ready.
 * @param {number} total — total number of questions in the quiz
 */
function initMCQ(total) {
  totalQuestions = total;
  updateView();
  startTimer();

  // Attach radio-change listeners to all option labels
  document.querySelectorAll('.option-radio').forEach(radio => {
    radio.addEventListener('change', handleOptionChange);
  });
}

/* ── Question Navigation ─────────────────────────────────────────────────── */

function navigateQuestion(direction) {
  const newIndex = currentQuestion + direction;
  if (newIndex < 0 || newIndex >= totalQuestions) return;
  currentQuestion = newIndex;
  updateView();
}

function goToQuestion(index) {
  currentQuestion = index;
  updateView();
}

function updateView() {
  // Show/hide question cards
  document.querySelectorAll('.question-card').forEach((card, i) => {
    card.classList.toggle('hidden', i !== currentQuestion);
  });

  // Progress bar
  const pct = ((currentQuestion + 1) / totalQuestions) * 100;
  const fill = document.getElementById('progress-fill');
  if (fill) fill.style.width = pct + '%';

  // Counter label
  const counter = document.getElementById('current-q');
  if (counter) counter.textContent = currentQuestion + 1;

  // Dots
  document.querySelectorAll('.dot').forEach((dot, i) => {
    dot.classList.toggle('dot--active', i === currentQuestion);
    dot.classList.toggle('dot--answered', !!answeredMap[i] && i !== currentQuestion);
  });

  // Prev / Next buttons
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  if (prevBtn) prevBtn.disabled = currentQuestion === 0;

  const isLast = currentQuestion === totalQuestions - 1;
  if (nextBtn) {
    nextBtn.textContent = isLast ? 'Review →' : 'Next →';
  }

  // Show submit area on last question
  const submitArea = document.getElementById('submit-area');
  if (submitArea) {
    submitArea.classList.toggle('hidden', !isLast);
    if (isLast) updateSubmitSummary();
  }
}

/* ── Answer Selection ────────────────────────────────────────────────────── */

function handleOptionChange(e) {
  const radio = e.target;
  const name  = radio.name;                         // "q0", "q1", ...
  const qIdx  = parseInt(name.replace('q', ''), 10);

  // Track in our map
  answeredMap[qIdx] = radio.value;

  // Update option label styles
  const optionsContainer = document.getElementById(`options-${qIdx}`);
  if (optionsContainer) {
    optionsContainer.querySelectorAll('.option-label').forEach(label => {
      label.classList.remove('selected');
    });
    const parentLabel = radio.closest('.option-label');
    if (parentLabel) parentLabel.classList.add('selected');
  }

  // Update dot for this question
  const dot = document.getElementById(`dot-${qIdx}`);
  if (dot && qIdx !== currentQuestion) dot.classList.add('dot--answered');

  updateSubmitSummary();
}

/* ── Submit Summary ──────────────────────────────────────────────────────── */

function updateSubmitSummary() {
  const answered  = Object.keys(answeredMap).length;
  const remaining = totalQuestions - answered;
  const summary   = document.getElementById('submit-summary');
  if (!summary) return;
  summary.innerHTML = `You have answered <strong>${answered}/${totalQuestions}</strong> questions.
    ${remaining > 0 ? `<br><span style="color:var(--warning)">⚠️ ${remaining} question(s) unanswered.</span>` : '<br><span style="color:var(--success)">✅ All questions answered!</span>'}`;
}

/* ── Timer ───────────────────────────────────────────────────────────────── */

function startTimer() {
  const display = document.getElementById('timer-display');
  if (!display) return;

  timerInterval = setInterval(() => {
    secondsLeft--;
    if (secondsLeft <= 0) {
      clearInterval(timerInterval);
      display.textContent = '00:00';
      autoSubmit();
      return;
    }

    const minutes = Math.floor(secondsLeft / 60);
    const seconds = secondsLeft % 60;
    display.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

    // Visual warnings
    if (secondsLeft <= 60) {
      display.classList.add('danger');
      display.classList.remove('warning');
    } else if (secondsLeft <= 5 * 60) {
      display.classList.add('warning');
    }
  }, 1000);
}

function autoSubmit() {
  const form = document.getElementById('mcq-form');
  if (form) {
    alert('⏰ Time is up! Your answers are being submitted automatically.');
    form.submit();
  }
}

/* ── Prevent accidental page exit during quiz ────────────────────────────── */
window.addEventListener('beforeunload', e => {
  if (Object.keys(answeredMap).length > 0) {
    e.preventDefault();
    e.returnValue = '';
  }
});
