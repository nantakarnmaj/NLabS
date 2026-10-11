/**
 * BreathQuest Game Engine Frontend
 * Manages activity interaction, patient monitor updates, accessible step reordering,
 * and immediate feedback handling.
 */

(function () {
  'use strict';

  // State elements
  const monitorSpo2 = document.getElementById('monitor-spo2');
  const monitorHr = document.getElementById('monitor-hr');
  const monitorRr = document.getElementById('monitor-rr');
  const monitorDistress = document.getElementById('monitor-distress');
  const feedbackModal = document.getElementById('feedback-modal');
  const feedbackBanner = document.getElementById('feedback-banner');
  const feedbackIconBox = document.getElementById('feedback-icon-box');
  const feedbackStatusBadge = document.getElementById('feedback-status-badge');
  const confettiCanvas = document.getElementById('confetti-canvas');
  const feedbackTitle = document.getElementById('feedback-title');
  const feedbackMessage = document.getElementById('feedback-message');
  const feedbackRationale = document.getElementById('feedback-rationale');
  const feedbackHint = document.getElementById('feedback-hint');
  const feedbackHintContainer = document.getElementById('feedback-hint-container');
  const feedbackActionBtn = document.getElementById('feedback-action-btn');
  const ariaAnnouncer = document.getElementById('aria-announcements');

  // Read configuration from data attributes
  const gameContainer = document.getElementById('game-container');
  if (!gameContainer) return;

  const runId = gameContainer.dataset.runId;
  const activityId = gameContainer.dataset.activityId;
  let currentRevision = parseInt(gameContainer.dataset.revision || '1', 10);
  const activityType = gameContainer.dataset.activityType;
  function getCsrfToken() {
    return (
      document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
      document.getElementById('csrf-token-fallback')?.value ||
      ''
    );
  }

  // Announce to screen readers
  function announce(msg) {
    if (ariaAnnouncer) {
      ariaAnnouncer.textContent = msg;
    }
  }

  // Generate unique idempotency key
  function generateIdempotencyKey() {
    return 'idem_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
  }

  // Update bedside patient monitor with animated highlight
  function updatePatientMonitor(vitals) {
    if (!vitals) return;

    if (monitorSpo2 && vitals.spo2 !== undefined) {
      animateValueChange(monitorSpo2, vitals.spo2 + '%');
      // Color-code based on SpO2 levels
      if (vitals.spo2 < 90) {
        monitorSpo2.className = 'text-2xl sm:text-3xl font-black font-mono text-red-400';
      } else if (vitals.spo2 < 94) {
        monitorSpo2.className = 'text-2xl sm:text-3xl font-black font-mono text-amber-400';
      } else {
        monitorSpo2.className = 'text-2xl sm:text-3xl font-black font-mono text-emerald-400';
      }
    }

    if (monitorHr && vitals.hr !== undefined) {
      animateValueChange(monitorHr, vitals.hr + ' bpm');
      if (vitals.hr < 50 || vitals.hr > 120) {
        monitorHr.className = 'text-2xl sm:text-3xl font-black font-mono text-red-400';
      } else {
        monitorHr.className = 'text-2xl sm:text-3xl font-black font-mono text-cyan-400';
      }
    }

    if (monitorRr && vitals.rr !== undefined) {
      animateValueChange(monitorRr, vitals.rr + ' /min');
    }

    if (monitorDistress && vitals.distress !== undefined) {
      const labels = ['สงบ/ปกติ', 'เล็กน้อย', 'ปานกลาง', 'รุนแรง', 'วิกฤต', 'รุนแรงมาก'];
      const text = labels[vitals.distress] || 'ปานกลาง';
      monitorDistress.textContent = text;
    }
  }

  function animateValueChange(element, newValue) {
    if (element.textContent !== newValue) {
      element.textContent = newValue;
      element.classList.add('scale-110', 'brightness-125');
      setTimeout(() => {
        element.classList.remove('scale-110', 'brightness-125');
      }, 300);
    }
  }

  // Synthesize pleasant, non-blocking Web Audio tones for feedback
  function playFeedbackSound(isSuccess) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      if (ctx.state === 'suspended') {
        ctx.resume();
      }

      if (isSuccess) {
        // Cheerful ascending 3-note arpeggio (C5 -> E5 -> G5)
        const notes = [523.25, 659.25, 783.99];
        notes.forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.09);

          gain.gain.setValueAtTime(0.001, ctx.currentTime + idx * 0.09);
          gain.gain.linearRampToValueAtTime(0.18, ctx.currentTime + idx * 0.09 + 0.02);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.09 + 0.28);

          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(ctx.currentTime + idx * 0.09);
          osc.stop(ctx.currentTime + idx * 0.09 + 0.3);
        });
      } else {
        // Gentle caution tone
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(260, ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(190, ctx.currentTime + 0.22);

        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.28);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.3);
      }
    } catch (_) {
      // Audio is optional and non-blocking
    }
  }

  // Lightweight zero-dependency celebration confetti burst
  function fireConfetti() {
    if (!confettiCanvas) return;
    const ctx = confettiCanvas.getContext('2d');
    if (!ctx) return;

    confettiCanvas.width = window.innerWidth;
    confettiCanvas.height = window.innerHeight;
    confettiCanvas.classList.remove('hidden');

    const particles = [];
    const colors = ['#10B981', '#06B6D4', '#3B82F6', '#F59E0B', '#EC4899', '#8B5CF6'];
    const count = 45;

    for (let i = 0; i < count; i++) {
      particles.push({
        x: confettiCanvas.width / 2 + (Math.random() - 0.5) * 160,
        y: confettiCanvas.height / 2 - 120 + (Math.random() - 0.5) * 100,
        vx: (Math.random() - 0.5) * 15,
        vy: -Math.random() * 8 - 4,
        size: Math.random() * 9 + 6,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        rSpeed: (Math.random() - 0.5) * 12,
        opacity: 1,
      });
    }

    let frame = 0;
    function animate() {
      ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
      let alive = false;

      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.35; // gravity
        p.vx *= 0.98; // drag
        p.rotation += p.rSpeed;
        p.opacity -= 0.013;

        if (p.opacity > 0 && p.y < confettiCanvas.height) {
          alive = true;
          ctx.save();
          ctx.globalAlpha = Math.max(0, p.opacity);
          ctx.translate(p.x, p.y);
          ctx.rotate((p.rotation * Math.PI) / 180);
          ctx.fillStyle = p.color;
          ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.7);
          ctx.restore();
        }
      });

      frame++;
      if (alive && frame < 90) {
        requestAnimationFrame(animate);
      } else {
        ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
        confettiCanvas.classList.add('hidden');
      }
    }
    requestAnimationFrame(animate);
  }

  // Display feedback modal
  function showFeedback(result) {
    if (!feedbackModal) return;

    // Immediately display modal so the user gets instant visual feedback
    feedbackModal.classList.remove('hidden');
    feedbackModal.classList.add('flex');

    if (feedbackTitle) {
      feedbackTitle.textContent = result.title || (result.success ? 'การปฏิบัติถูกต้อง' : 'ข้อควรระวังทางการพยาบาล');
    }
    if (feedbackMessage) {
      feedbackMessage.textContent = result.message || '';
    }

    if (feedbackRationale) {
      feedbackRationale.textContent = result.clinical_rationale || '';
      if (feedbackRationale.parentElement) {
        if (result.clinical_rationale) {
          feedbackRationale.parentElement.classList.remove('hidden');
        } else {
          feedbackRationale.parentElement.classList.add('hidden');
        }
      }
    }

    if (feedbackHint) {
      feedbackHint.textContent = result.hint || '';
    }
    if (feedbackHintContainer) {
      if (result.hint && !result.success) {
        feedbackHintContainer.classList.remove('hidden');
      } else {
        feedbackHintContainer.classList.add('hidden');
      }
    }

    if (result.success) {
      if (feedbackBanner) {
        feedbackBanner.className = 'absolute top-0 inset-x-0 h-2.5 bg-gradient-to-r from-emerald-500 via-teal-400 to-sky-400';
      }
      if (feedbackIconBox) {
        feedbackIconBox.innerHTML = `
          <div class="w-18 h-18 sm:w-20 sm:h-20 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 text-white flex items-center justify-center shadow-lg shadow-emerald-500/30 ring-8 ring-emerald-100 animate-bounce">
            <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        `;
      }
      if (feedbackStatusBadge) {
        feedbackStatusBadge.className = 'inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs sm:text-sm font-black tracking-wide bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs';
        feedbackStatusBadge.innerHTML = '<span>🎉</span><span>ถูกต้องยอดเยี่ยม! (EXCELLENT!)</span>';
      }

      if (feedbackActionBtn) {
        const nextLabel = result.is_mission_completed ? 'ดูการสะท้อนคิดปิดภารกิจ (View Debrief)' : 'ไปยังขั้นตอนถัดไป (Next Step)';
        feedbackActionBtn.innerHTML = `<span>${nextLabel}</span> <svg class="w-5 h-5 ml-1 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>`;
        feedbackActionBtn.className = 'w-full py-4 px-6 rounded-2xl font-black text-base text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-sky-600 hover:from-emerald-500 hover:via-teal-500 hover:to-sky-500 active:scale-[0.98] shadow-lg shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer touch-target';
        feedbackActionBtn.onclick = function () {
          window.location.reload();
        };
      }

      try {
        playFeedbackSound(true);
      } catch (e) {
        console.warn('Audio non-blocking note:', e);
      }
      try {
        fireConfetti();
      } catch (e) {
        console.warn('Confetti non-blocking note:', e);
      }
    } else {
      if (feedbackBanner) {
        feedbackBanner.className = 'absolute top-0 inset-x-0 h-2.5 bg-gradient-to-r from-amber-500 via-orange-400 to-rose-400';
      }
      if (feedbackIconBox) {
        feedbackIconBox.innerHTML = `
          <div class="w-18 h-18 sm:w-20 sm:h-20 rounded-full bg-gradient-to-tr from-amber-500 to-rose-400 text-white flex items-center justify-center shadow-lg shadow-amber-500/30 ring-8 ring-amber-100 animate-pulse">
            <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        `;
      }
      if (feedbackStatusBadge) {
        feedbackStatusBadge.className = 'inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs sm:text-sm font-black tracking-wide bg-amber-100 text-amber-900 border border-amber-300 shadow-2xs';
        feedbackStatusBadge.innerHTML = '<span>⚠️</span><span>ข้อควรระวังความปลอดภัย (SAFETY ALERT)</span>';
      }

      if (feedbackActionBtn) {
        if (result.reload_on_dismiss) {
          feedbackActionBtn.innerHTML = '<span>โหลดข้อมูลขั้นตอนล่าสุด (Refresh Step)</span>';
          feedbackActionBtn.onclick = function () {
            window.location.reload();
          };
        } else {
          feedbackActionBtn.innerHTML = '<span>ลองใหม่อีกครั้ง (Try Again Safely)</span>';
          feedbackActionBtn.onclick = function () {
            closeFeedback();
          };
        }
        feedbackActionBtn.className = 'w-full py-3.5 px-6 rounded-2xl font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 active:scale-[0.98] transition-all flex items-center justify-center gap-2 cursor-pointer touch-target';
      }

      try {
        playFeedbackSound(false);
      } catch (e) {
        console.warn('Audio non-blocking note:', e);
      }
    }

    announce((result.title || '') + '. ' + (result.message || ''));
  }

  function closeFeedback() {
    if (!feedbackModal) return;
    feedbackModal.classList.add('hidden');
    feedbackModal.classList.remove('flex');
  }

  // Initialize Sequence Activity with SortableJS and accessible keyboard reordering
  function initSequence() {
    const sequenceList = document.getElementById('sequence-list');
    if (!sequenceList) return;

    // 1. Initialize SortableJS for drag-and-drop
    if (window.Sortable) {
      new window.Sortable(sequenceList, {
        animation: 150,
        ghostClass: 'opacity-50',
        chosenClass: 'bg-sky-100',
        handle: '.drag-handle',
        onEnd: function () {
          announce('จัดลำดับขั้นตอนใหม่เรียบร้อยแล้ว');
        },
      });
    }

    // 2. Attach Move Up / Move Down buttons for accessibility
    sequenceList.addEventListener('click', function (e) {
      const btn = e.target.closest('button[data-action]');
      if (!btn) return;

      const item = btn.closest('li[data-step-key]');
      if (!item) return;

      if (btn.dataset.action === 'move-up') {
        const prev = item.previousElementSibling;
        if (prev) {
          sequenceList.insertBefore(item, prev);
          item.focus();
          announce('เลื่อนขั้นตอนขึ้นแล้ว');
        }
      } else if (btn.dataset.action === 'move-down') {
        const next = item.nextElementSibling;
        if (next) {
          sequenceList.insertBefore(next, item);
          item.focus();
          announce('เลื่อนขั้นตอนลงแล้ว');
        }
      }
    });
  }

  // Initialize Multi-selection Cards
  function initSelection() {
    const selectionCards = document.querySelectorAll('.selection-card');
    selectionCards.forEach((card) => {
      function toggleCard() {
        const isChecked = card.getAttribute('aria-checked') === 'true';
        const newChecked = !isChecked;
        card.setAttribute('aria-checked', newChecked ? 'true' : 'false');

        const checkbox = card.querySelector('input[type="checkbox"]');
        if (checkbox) {
          checkbox.checked = newChecked;
        }

        const checkmarkBox = card.querySelector('.checkmark-box');
        const checkmarkIcon = card.querySelector('.checkmark-icon');

        if (newChecked) {
          card.classList.add('border-[#1296DB]', 'bg-sky-50', 'ring-2', 'ring-sky-200');
          card.classList.remove('border-[#DCEAF7]', 'bg-white');
          if (checkmarkBox) {
            checkmarkBox.classList.add('bg-[#1296DB]', 'border-[#1296DB]');
            checkmarkBox.classList.remove('bg-white', 'border-slate-300');
          }
          if (checkmarkIcon) {
            checkmarkIcon.classList.remove('hidden');
          }
        } else {
          card.classList.remove('border-[#1296DB]', 'bg-sky-50', 'ring-2', 'ring-sky-200');
          card.classList.add('border-[#DCEAF7]', 'bg-white');
          if (checkmarkBox) {
            checkmarkBox.classList.remove('bg-[#1296DB]', 'border-[#1296DB]');
            checkmarkBox.classList.add('bg-white', 'border-slate-300');
          }
          if (checkmarkIcon) {
            checkmarkIcon.classList.add('hidden');
          }
        }
      }

      card.addEventListener('click', toggleCard);
      card.addEventListener('keydown', function (e) {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          toggleCard();
        }
      });
    });
  }

  // Handle Activity Submission
  async function submitPayload(payload) {
    const submitBtn = document.getElementById('submit-btn');
    let originalBtnHtml = '';
    if (submitBtn) {
      originalBtnHtml = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.classList.add('opacity-75', 'cursor-wait');
      submitBtn.innerHTML = `
        <span class="inline-flex items-center gap-2">
          <svg class="animate-spin h-4 w-4 text-white shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span>กำลังบันทึกคำตอบ...</span>
        </span>
      `;
    }

    const idempotencyKey = generateIdempotencyKey();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000); // 20s safety timeout

    try {
      const response = await fetch(`/api/runs/${runId}/activities/${activityId}/submit`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          payload: payload,
          idempotency_key: idempotencyKey,
          expected_revision: currentRevision,
        }),
      });

      clearTimeout(timeoutId);

      let result;
      try {
        result = await response.json();
      } catch (jsonErr) {
        throw new Error('เซิร์ฟเวอร์ตอบกลับด้วยรูปแบบที่ไม่ถูกต้อง (HTTP ' + response.status + ')');
      }

      if (result.error) {
        if (result.error.code === 'stale_state') {
          showFeedback({
            success: false,
            reload_on_dismiss: true,
            title: 'ข้อมูลในหน้านี้มีการเปลี่ยนแปลง',
            message: 'เซิร์ฟเวอร์มีข้อมูลสถานะที่ใหม่กว่า กำลังโหลดหน้าปัจจุบัน...',
            hint: 'กดปุ่มด้านล่างเพื่อรีเฟรชข้อมูลขั้นตอนล่าสุด',
          });
          return;
        }
        if (result.error.code === 'out_of_order') {
          showFeedback({
            success: false,
            reload_on_dismiss: true,
            title: 'ลำดับขั้นตอนไม่ตรงกับสถานะปัจจุบัน',
            message: result.error.message || 'โปรดทำขั้นตอนก่อนหน้าให้เสร็จสิ้นก่อน',
            hint: 'กดปุ่มด้านล่างเพื่อไปยังขั้นตอนที่ถูกต้อง',
          });
          return;
        }
        showFeedback({
          success: false,
          title: 'ไม่สามารถดำเนินการต่อได้',
          message: result.error.message || 'เกิดข้อผิดพลาดในการตรวจสอบคำตอบ',
          hint: 'โปรดตรวจสอบข้อมูลและลองใหม่อีกครั้ง',
        });
        return;
      }

      if (result.revision) {
        currentRevision = result.revision;
      }

      if (result.patient_state) {
        updatePatientMonitor(result.patient_state);
      }

      showFeedback(result);
    } catch (err) {
      clearTimeout(timeoutId);
      console.error('Submission error:', err);
      const isTimeout = err.name === 'AbortError';
      showFeedback({
        success: false,
        title: isTimeout ? 'การเชื่อมต่อหมดเวลา (Timeout)' : 'เกิดข้อผิดพลาดในการเชื่อมต่อ',
        message: isTimeout
          ? 'เซิร์ฟเวอร์ใช้เวลาตอบสนองนานเกินไป โปรดกดลองใหม่อีกครั้ง'
          : (err.message || 'ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์จำลองสถานการณ์ได้ โปรดลองอีกครั้ง'),
        hint: 'โปรดตรวจสอบการเชื่อมต่ออินเทอร์เน็ตของคุณ หรือกดลองใหม่อีกครั้ง',
      });
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-75', 'opacity-50', 'cursor-wait', 'cursor-not-allowed');
        if (originalBtnHtml) {
          submitBtn.innerHTML = originalBtnHtml;
        }
      }
    }
  }

  // Wire submission form/button
  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', function () {
      let payload = {};

      if (activityType === 'intro' || activityType === 'outcome') {
        payload = { acknowledged: true };
      } else if (activityType === 'sequence') {
        const stepItems = document.querySelectorAll('#sequence-list li[data-step-key]');
        const keys = Array.from(stepItems).map((el) => el.dataset.stepKey);
        payload = { ordered_keys: keys };
      } else if (activityType === 'decision' || activityType === 'troubleshooting') {
        const selectedRadio = document.querySelector('input[name="choice"]:checked');
        if (!selectedRadio) {
          alert('กรุณาเลือกคำตอบเพื่อดำเนินการต่อ');
          return;
        }
        payload = { chosen_key: selectedRadio.value };
      } else if (activityType === 'matching') {
        const selects = document.querySelectorAll('.matching-select');
        const pairs = {};
        selects.forEach((sel) => {
          const promptKey = sel.dataset.promptKey;
          if (sel.value) {
            pairs[promptKey] = sel.value;
          }
        });
        payload = { pairs: pairs };
      } else if (activityType === 'debrief') {
        const textarea = document.getElementById('reflection-input');
        const text = textarea ? textarea.value.trim() : '';
        if (text.length < 5) {
          alert('กรุณาพิมพ์การสะท้อนคิดของคุณก่อนส่งภารกิจ');
          return;
        }
        payload = { reflection_text: text };
      } else {
        // Multi-select
        const checkedBoxes = document.querySelectorAll('.selection-card[aria-checked="true"]');
        const selectedKeys = Array.from(checkedBoxes).map((card) => card.dataset.optionKey);
        if (selectedKeys.length === 0) {
          alert('กรุณาเลือกอย่างน้อย 1 ตัวเลือก');
          return;
        }
        payload = { selected_keys: selectedKeys };
      }

      submitPayload(payload);
    });
  }

  // Initialize interactive components based on activity type
  if (activityType === 'sequence') {
    initSequence();
  } else if (
    activityType === 'clinical_cues' ||
    activityType === 'equipment_select' ||
    activityType === 'medication_check' ||
    activityType === 'safety_check' ||
    activityType === 'aftercare'
  ) {
    initSelection();
  }

  // Escape key closes modal
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && feedbackModal && !feedbackModal.classList.contains('hidden')) {
      closeFeedback();
    }
  });
})();
