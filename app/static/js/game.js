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
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

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

  // Display feedback modal
  function showFeedback(result) {
    if (!feedbackModal) return;

    feedbackTitle.textContent = result.title || (result.success ? 'การปฏิบัติถูกต้อง' : 'ข้อควรระวังทางการพยาบาล');
    feedbackMessage.textContent = result.message || '';

    if (result.clinical_rationale) {
      feedbackRationale.textContent = result.clinical_rationale;
      feedbackRationale.parentElement.classList.remove('hidden');
    } else {
      feedbackRationale.parentElement.classList.add('hidden');
    }

    if (result.hint && !result.success) {
      feedbackHint.textContent = result.hint;
      feedbackHintContainer.classList.remove('hidden');
    } else {
      feedbackHintContainer.classList.add('hidden');
    }

    if (result.success) {
      feedbackActionBtn.textContent = result.is_mission_completed ? 'ดูการสะท้อนคิดปิดภารกิจ (View Debrief)' : 'ไปยังขั้นตอนถัดไป (Next Step)';
      feedbackActionBtn.className = 'w-full py-3 px-6 rounded-xl font-bold text-white bg-sky-600 hover:bg-sky-700 transition shadow-sm';
      feedbackActionBtn.onclick = function () {
        window.location.reload();
      };
    } else {
      feedbackActionBtn.textContent = 'ลองใหม่อีกครั้ง (Try Again Safely)';
      feedbackActionBtn.className = 'w-full py-3 px-6 rounded-xl font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 transition shadow-xs';
      feedbackActionBtn.onclick = function () {
        closeFeedback();
      };
    }

    feedbackModal.classList.remove('hidden');
    feedbackModal.classList.add('flex');
    announce(result.title + '. ' + result.message);
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
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
    }

    const idempotencyKey = generateIdempotencyKey();

    try {
      const response = await fetch(`/api/runs/${runId}/activities/${activityId}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || '',
        },
        body: JSON.stringify({
          payload: payload,
          idempotency_key: idempotencyKey,
          expected_revision: currentRevision,
        }),
      });

      const result = await response.json();

      if (result.error) {
        if (result.error.code === 'stale_state') {
          alert('ข้อมูลในหน้านี้มีการเปลี่ยนแปลง กำลังโหลดข้อมูลล่าสุด...');
          window.location.reload();
          return;
        }
        showFeedback({
          success: false,
          title: 'ไม่สามารถดำเนินการต่อได้',
          message: result.error.message,
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
      console.error('Submission error:', err);
      showFeedback({
        success: false,
        title: 'เกิดข้อผิดพลาดในการเชื่อมต่อ',
        message: 'ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์จำลองสถานการณ์ได้ โปรดลองอีกครั้ง',
        hint: 'โปรดตรวจสอบการเชื่อมต่ออินเทอร์เน็ตของคุณ',
      });
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
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
