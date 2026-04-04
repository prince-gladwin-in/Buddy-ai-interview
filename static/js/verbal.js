/**
 * verbal.js — Verbal interview controller.
 * Handles: Buddy persona flow, Web Speech API transcription,
 * answer submission to /api/verbal/score, and question progression.
 */

let candidateId         = null;
let questionsData       = [];   // Array of question strings
let questionsFull       = [];   // Array of {question, ideal_answer} objects
let currentQuestionIdx  = -1;   // -1 = not started
let isRecording         = false;
let recognition         = null;
let transcript          = '';

/* ─────────────────────────────────────────────────────────────────────────── */
/* Entry Point                                                                 */
/* ─────────────────────────────────────────────────────────────────────────── */

/**
 * @param {number} cid         — Candidate ID from Flask
 * @param {string[]} qData     — Array of question strings
 * @param {object[]} qFull     — Array of {question, ideal_answer}
 */
function initVerbalInterview(cid, qData, qFull) {
  candidateId   = cid;
  questionsData = qData;
  questionsFull = qFull;
  initSpeechRecognition();
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Speech Recognition                                                          */
/* ─────────────────────────────────────────────────────────────────────────── */

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    const statusEl = document.getElementById('mic-status');
    if (statusEl) statusEl.textContent = "Voice input not supported — please type your answer.";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous    = true;
  recognition.interimResults = true;
  recognition.lang          = 'en-US';

  recognition.onstart = () => {
    isRecording = true;
    const micBtn  = document.getElementById('mic-btn');
    const micIcon = document.getElementById('mic-icon');
    const status  = document.getElementById('mic-status');
    if (micBtn)  micBtn.classList.add('recording');
    if (micIcon) micIcon.textContent = '⏹️';
    if (status)  status.textContent = '🔴 Recording… speak now';
  };

  recognition.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript   = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const text = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += text + ' ';
      } else {
        interimTranscript += text;
      }
    }

    if (finalTranscript) transcript += finalTranscript;

    const textarea = document.getElementById('answer-textarea');
    if (textarea) textarea.value = (transcript + interimTranscript).trim();
  };

  recognition.onend = () => {
    isRecording = false;
    const micBtn  = document.getElementById('mic-btn');
    const micIcon = document.getElementById('mic-icon');
    const status  = document.getElementById('mic-status');
    if (micBtn)  micBtn.classList.remove('recording');
    if (micIcon) micIcon.textContent = '🎙️';
    if (status)  status.textContent = 'Recording stopped. Edit below or re-record.';
  };

  recognition.onerror = (event) => {
    console.warn('[Speech] Error:', event.error);
    isRecording = false;
    const status = document.getElementById('mic-status');
    if (status) status.textContent = `Mic error: ${event.error}. Please type your answer.`;
  };
}

function toggleRecording() {
  if (!recognition) return;
  if (isRecording) {
    recognition.stop();
  } else {
    transcript = '';
    const textarea = document.getElementById('answer-textarea');
    if (textarea) textarea.value = '';
    try { recognition.start(); } catch (e) { console.warn('[Speech] Start error:', e); }
  }
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Interview Flow                                                              */
/* ─────────────────────────────────────────────────────────────────────────── */

function startInterview() {
  // Hide Buddy intro bubble and start button
  const startArea   = document.getElementById('start-area');
  const buddyBubble = document.getElementById('buddy-bubble');
  if (startArea)   startArea.style.display = 'none';
  if (buddyBubble) buddyBubble.style.display = 'none';

  currentQuestionIdx = 0;
  showQuestion(0);
}

function showQuestion(index) {
  const question = questionsData[index];

  // Update question display
  const qDisplay = document.getElementById('question-display');
  const qNumber  = document.getElementById('verbal-q-number');
  const qText    = document.getElementById('verbal-question-text');
  if (qDisplay) qDisplay.style.display = 'block';
  if (qNumber)  qNumber.textContent = `Q${index + 1} of ${questionsData.length}`;
  if (qText)    qText.textContent = question;

  // Buddy says the question
  setBuddyMessage(`Here's question ${index + 1}: "${question}" — take your time and share what you think! 😊`);

  // Update counter and progress bar
  const counter = document.getElementById('q-counter');
  if (counter) counter.textContent = `Question ${index + 1} / ${questionsData.length}`;
  const progressFill = document.getElementById('verbal-progress-fill');
  if (progressFill) {
    progressFill.style.width = ((index + 1) / questionsData.length * 100) + '%';
  }

  // Show answer section, reset state
  const answerSection = document.getElementById('answer-section');
  const reflection    = document.getElementById('buddy-reflection');
  if (answerSection) answerSection.style.display = 'block';
  if (reflection)    reflection.classList.add('hidden');

  // Reset transcript and textarea
  transcript = '';
  const textarea = document.getElementById('answer-textarea');
  if (textarea) textarea.value = '';

  // Reset mic status
  const status = document.getElementById('mic-status');
  if (status) status.textContent = 'Click the mic to start speaking';
}

function setBuddyMessage(text) {
  const msgEl = document.getElementById('buddy-message');
  if (!msgEl) return;
  msgEl.style.opacity = '0';
  setTimeout(() => {
    msgEl.innerHTML = text;
    msgEl.style.transition = 'opacity 0.4s';
    msgEl.style.opacity = '1';
  }, 200);
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Answer Submission                                                           */
/* ─────────────────────────────────────────────────────────────────────────── */

async function submitAnswer() {
  if (isRecording) recognition.stop();

  const textarea = document.getElementById('answer-textarea');
  const answer   = textarea ? textarea.value.trim() : '';

  if (!answer) {
    alert('Please provide an answer before submitting. You can speak or type!');
    return;
  }

  // Show loading state
  const submitBtn  = document.getElementById('submit-answer-btn');
  const submitText = document.getElementById('submit-answer-text');
  const spinner    = document.getElementById('submit-answer-spinner');
  if (submitBtn) submitBtn.disabled = true;
  if (submitText) submitText.textContent = 'Evaluating…';
  if (spinner)   spinner.classList.remove('hidden');

  const currentQ = questionsFull[currentQuestionIdx];

  try {
    const response = await fetch('/api/verbal/score', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        candidate_id:   candidateId,
        question_index: currentQuestionIdx,
        question:       currentQ.question,
        answer:         answer,
        ideal_answer:   currentQ.ideal_answer
      })
    });

    const data = await response.json();

    if (data.success) {
      showReflection(data);
    } else {
      alert('Scoring error. Please try again.');
    }
  } catch (err) {
    console.error('[Verbal] Submit error:', err);
    alert('Network error. Please check your connection and try again.');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
    if (submitText) submitText.textContent = 'Submit Answer';
    if (spinner) spinner.classList.add('hidden');
  }
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Buddy Reflection After Each Answer                                          */
/* ─────────────────────────────────────────────────────────────────────────── */

function showReflection(data) {
  // Hide answer section
  const answerSection = document.getElementById('answer-section');
  if (answerSection) answerSection.style.display = 'none';

  // Show reflection
  const reflection = document.getElementById('buddy-reflection');
  const scoreEl    = document.getElementById('reflection-score');
  const msgEl      = document.getElementById('reflection-message');
  const nextBtn    = document.getElementById('next-question-btn');
  const finishBtn  = document.getElementById('finish-btn');

  if (!reflection) return;

  if (scoreEl) scoreEl.textContent = `Score: ${data.score_pct} — ${data.label}`;
  if (msgEl)   msgEl.textContent   = data.reflection;

  // Buddy also says the reflection
  setBuddyMessage(data.reflection);

  const isLast = currentQuestionIdx === questionsData.length - 1;
  if (nextBtn)   nextBtn.classList.toggle('hidden', isLast);
  if (finishBtn) finishBtn.classList.toggle('hidden', !isLast);

  reflection.classList.remove('hidden');

  // Animate score display
  if (scoreEl) {
    scoreEl.style.transform = 'scale(0.8)';
    scoreEl.style.opacity   = '0';
    setTimeout(() => {
      scoreEl.style.transition = 'all 0.4s cubic-bezier(0.34,1.56,0.64,1)';
      scoreEl.style.transform = 'scale(1)';
      scoreEl.style.opacity   = '1';
    }, 100);
  }
}

function nextQuestion() {
  currentQuestionIdx++;
  if (currentQuestionIdx < questionsData.length) {
    showQuestion(currentQuestionIdx);
  }
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Finish Interview                                                            */
/* ─────────────────────────────────────────────────────────────────────────── */

async function finishInterview() {
  // Stop face monitor
  if (typeof stopFaceMonitor === 'function') stopFaceMonitor();

  setBuddyMessage("🎉 You've completed the interview! You were amazing — I'm so proud of you! Your results are being prepared right now. See you on the other side! 🌟");

  try {
    const response = await fetch('/api/verbal/complete', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ candidate_id: candidateId })
    });
    const data = await response.json();
    if (data.redirect_url) {
      setTimeout(() => { window.location.href = data.redirect_url; }, 2500);
    }
  } catch (err) {
    console.error('[Verbal] Finish error:', err);
    setTimeout(() => { window.location.href = `/results/${candidateId}`; }, 2500);
  }
}
