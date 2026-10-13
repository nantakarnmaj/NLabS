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
  const monitorBreathSound = document.getElementById('monitor-breath-sound');
  const monitorSecretions = document.getElementById('monitor-secretions');
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

  // Clinical terminology safety override: prevent any stale cache or DB state from showing 'เสมหะเดือด'
  function enforceClinicalTerminology() {
    if (monitorBreathSound) {
      const current = monitorBreathSound.textContent || '';
      if (current.includes('เดือด') || current.toLowerCase().includes('coarse rhonchi')) {
        monitorBreathSound.textContent = 'เสมหะมาก (Rhonchi)';
      }
    }
    if (monitorSecretions) {
      const currentSec = monitorSecretions.textContent || '';
      if (currentSec.includes('(Copious)')) {
        monitorSecretions.textContent = currentSec.replace('(Copious)', '').trim();
      }
    }
  }
  enforceClinicalTerminology();
  document.addEventListener('DOMContentLoaded', enforceClinicalTerminology);

  // Read configuration from data attributes
  const gameContainer = document.getElementById('game-container');
  if (!gameContainer) return;

  const runId = gameContainer.dataset.runId;
  const activityId = gameContainer.dataset.activityId;
  let currentRevision = parseInt(gameContainer.dataset.revision || '1', 10);
  const activityType = gameContainer.dataset.activityType;
  const isReview = gameContainer.dataset.isReview === 'true';
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
      } else if (vitals.hr > 90) {
        monitorHr.className = 'text-2xl sm:text-3xl font-black font-mono text-amber-400';
      } else {
        monitorHr.className = 'text-2xl sm:text-3xl font-black font-mono text-cyan-400';
      }
    }

    if (monitorRr && vitals.rr !== undefined) {
      animateValueChange(monitorRr, vitals.rr + ' /min');
      if (vitals.rr > 24) {
        monitorRr.className = 'text-2xl sm:text-3xl font-black font-mono text-red-400';
      } else if (vitals.rr > 20) {
        monitorRr.className = 'text-2xl sm:text-3xl font-black font-mono text-amber-400';
      } else {
        monitorRr.className = 'text-2xl sm:text-3xl font-black font-mono text-cyan-300';
      }
    }

    if (monitorDistress && vitals.distress !== undefined) {
      if (vitals.distress >= 3) {
        monitorDistress.className = 'px-3 py-1 rounded-full text-xs sm:text-sm font-bold bg-red-50 border border-red-300 text-red-800 flex items-center gap-1.5 shadow-2xs';
        monitorDistress.innerHTML = '<span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>วิกฤต/หายใจลำบากมาก (Severe Distress)';
      } else if (vitals.distress > 0) {
        monitorDistress.className = 'px-3 py-1 rounded-full text-xs sm:text-sm font-bold bg-amber-50 border border-amber-300 text-amber-800 flex items-center gap-1.5 shadow-2xs';
        monitorDistress.innerHTML = '<span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>หายใจลำบากปานกลาง (Moderate Distress)';
      } else {
        monitorDistress.className = 'px-3 py-1 rounded-full text-xs sm:text-sm font-bold bg-emerald-50 border border-emerald-300 text-emerald-800 flex items-center gap-1.5 shadow-2xs';
        monitorDistress.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>คงที่ / สงบ (Stable / Calm)';
      }
    }

    if (monitorBreathSound && vitals.breath_sound !== undefined) {
      const bsRaw = String(vitals.breath_sound || '');
      const bsMap = {
        'coarse_rhonchi': 'เสมหะมาก (Rhonchi)',
        'rhonchi': 'เสมหะมาก (Rhonchi)',
        'expiratory_wheezing': 'เสียงหวีด (Expiratory Wheezes)',
        'bilateral_wheezes_and_rhonchi': 'เสียงหวีด & เสมหะ (Wheezes & Rhonchi)',
        'bilateral_basal_crackles': 'เสียงกรอบแกรบ (Basal Crackles)',
        'clear': 'เสียงปอดโปร่งดี (Clear)',
        'clear_bilateral': 'เสียงปอดโปร่งดี (Clear)',
      };
      let text = bsMap[vitals.breath_sound];
      if (!text) {
        if (bsRaw.includes('เดือด') || bsRaw.toLowerCase().includes('rhonchi') || bsRaw.includes('เสมหะมาก')) {
          text = 'เสมหะมาก (Rhonchi)';
        } else if (bsRaw.toLowerCase().includes('clear')) {
          text = 'เสียงปอดโปร่งดี (Clear)';
        } else {
          text = vitals.breath_sound;
        }
      }
      monitorBreathSound.textContent = text;
    }

    if (monitorSecretions && vitals.secretions !== undefined) {
      const secMap = {
        'copious': 'เสมหะ: มาก/เหนียว',
        'copious_thick': 'เสมหะ: มาก/เหนียว',
        'moderate': 'เสมหะ: ปานกลาง (Moderate)',
        'minimal': 'เสมหะ: เล็กน้อย (Minimal)',
        'minimal/clear': 'เสมหะ: เล็กน้อย (Minimal)',
        'none': 'เสมหะ: ไม่มี (None)',
        'clear': 'เสมหะ: ไม่มี (None)',
      };
      monitorSecretions.textContent = secMap[vitals.secretions] || ('เสมหะ: ' + vitals.secretions);
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

  // Inline SVG definitions for guaranteed, zero-latency badge rendering without HTTP/Safari image decoder failures
  const BADGE_INLINE_SVGS = {
    nebulizer: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%" class="w-full h-full object-contain filter drop-shadow-md">
      <defs>
        <linearGradient id="bg-neb-modal" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#7c3aed"/>
          <stop offset="100%" stop-color="#6d28d9"/>
        </linearGradient>
      </defs>
      <polygon points="60,8 108,24 108,72 60,112 12,72 12,24" fill="url(#bg-neb-modal)" stroke="#c4b5fd" stroke-width="3" stroke-linejoin="round"/>
      <polygon points="60,16 100,30 100,68 60,102 20,68 20,30" fill="#0f172a" opacity="0.45"/>
      <g fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
        <path d="M52,62 L68,62 L65,85 L55,85 Z" fill="#c4b5fd" fill-opacity="0.3"/>
        <path d="M60,85 L60,94" stroke-width="3"/>
        <path d="M46,55 L74,55 L74,62 L46,62 Z" fill="#ffffff"/>
        <path d="M40,58.5 L46,58.5" stroke-width="4"/>
        <path d="M40,54 Q32,46 36,36 Q42,26 52,32" stroke="#a78bfa" stroke-width="2.5" stroke-dasharray="3 3"/>
        <path d="M42,50 Q48,36 60,34 Q70,32 76,40" stroke="#c4b5fd" stroke-width="2.5"/>
        <circle cx="58" cy="42" r="2.5" fill="#facc15" stroke="none"/>
        <circle cx="70" cy="36" r="2" fill="#facc15" stroke="none"/>
        <circle cx="48" cy="34" r="2" fill="#facc15" stroke="none"/>
      </g>
    </svg>`,
    oxygen: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%" class="w-full h-full object-contain filter drop-shadow-md">
      <defs>
        <linearGradient id="bg-oxygen-modal" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#059669"/>
          <stop offset="100%" stop-color="#047857"/>
        </linearGradient>
      </defs>
      <polygon points="60,8 108,24 108,72 60,112 12,72 12,24" fill="url(#bg-oxygen-modal)" stroke="#6ee7b7" stroke-width="3" stroke-linejoin="round"/>
      <polygon points="60,16 100,30 100,68 60,102 20,68 20,30" fill="#0f172a" opacity="0.45"/>
      <g transform="translate(60,60)">
        <circle cx="0" cy="0" r="28" fill="none" stroke="#a7f3d0" stroke-width="2.5" stroke-dasharray="4 2"/>
        <path d="M-6,-20 L6,-20 L6,-6 L20,-6 L20,6 L6,6 L6,20 L-6,20 L-6,6 L-20,6 L-20,-6 L-6,-6 Z" fill="#ffffff"/>
        <text x="0" y="5" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="900" fill="#047857" text-anchor="middle">O₂</text>
      </g>
      <polygon points="32,32 34,36 38,37 35,40 36,44 32,42 28,44 29,40 26,37 30,36" fill="#facc15"/>
      <polygon points="88,32 90,36 94,37 91,40 92,44 88,42 84,44 85,40 82,37 86,36" fill="#facc15"/>
    </svg>`,
    airway: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%" class="w-full h-full object-contain filter drop-shadow-md">
      <defs>
        <linearGradient id="bg-airway-modal" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0284c7"/>
          <stop offset="100%" stop-color="#0369a1"/>
        </linearGradient>
      </defs>
      <polygon points="60,8 108,24 108,72 60,112 12,72 12,24" fill="url(#bg-airway-modal)" stroke="#7dd3fc" stroke-width="3" stroke-linejoin="round"/>
      <polygon points="60,16 100,30 100,68 60,102 20,68 20,30" fill="#0f172a" opacity="0.45"/>
      <g fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M60,30 L60,50" />
        <path d="M54,34 L66,34" stroke-width="2.5" />
        <path d="M54,40 L66,40" stroke-width="2.5" />
        <path d="M54,46 L66,46" stroke-width="2.5" />
        <path d="M60,50 Q48,54 42,66 Q36,80 48,88 Q56,92 58,82 Q60,68 52,60" fill="#38bdf8" fill-opacity="0.25"/>
        <path d="M60,50 Q72,54 78,66 Q84,80 72,88 Q64,92 62,82 Q60,68 68,60" fill="#38bdf8" fill-opacity="0.25"/>
      </g>
      <polygon points="60,22 62,26 66,27 63,30 64,34 60,32 56,34 57,30 54,27 58,26" fill="#facc15"/>
    </svg>`,
    rescue: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%" class="w-full h-full object-contain filter drop-shadow-md">
      <defs>
        <linearGradient id="bg-rescue-modal" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#dc2626"/>
          <stop offset="100%" stop-color="#991b1b"/>
        </linearGradient>
      </defs>
      <polygon points="60,8 108,24 108,72 60,112 12,72 12,24" fill="url(#bg-rescue-modal)" stroke="#fca5a5" stroke-width="3" stroke-linejoin="round"/>
      <polygon points="60,16 100,30 100,68 60,102 20,68 20,30" fill="#0f172a" opacity="0.45"/>
      <g>
        <path d="M60,82 C60,82 32,64 32,46 C32,36 40,30 48,30 C54,30 58,34 60,38 C62,34 66,30 72,30 C80,30 88,36 88,46 C88,64 60,82 60,82 Z" fill="#ef4444" stroke="#ffffff" stroke-width="2.5"/>
        <path d="M26,52 L42,52 L46,42 L52,64 L58,38 L64,58 L68,48 L72,52 L94,52" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        <polygon points="60,18 63,24 69,25 64,29 66,35 60,32 54,35 56,29 51,25 57,24" fill="#facc15" stroke="#ca8a04" stroke-width="1"/>
      </g>
    </svg>`
  };

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
      const roomNumStr = String(gameContainer.dataset.roomNumber || '');
      const hasBadge = !!(
        result.badge_awarded ||
        result.is_mission_completed ||
        result.title?.includes('เหรียญ') ||
        result.message?.includes('เหรียญ')
      );

      let badgeKey = result.badge_awarded?.icon || gameContainer.dataset.badgeIcon;
      if (!badgeKey) {
        if (roomNumStr.includes('503')) badgeKey = 'nebulizer';
        else if (roomNumStr.includes('502')) badgeKey = 'oxygen';
        else if (roomNumStr.includes('501')) badgeKey = 'airway';
        else if (roomNumStr.includes('504')) badgeKey = 'rescue';
        else badgeKey = 'nebulizer';
      }
      const inlineBadgeSvg = BADGE_INLINE_SVGS[badgeKey] || BADGE_INLINE_SVGS.nebulizer;
      const badgeImgUrl = result.badge_awarded?.image_url || gameContainer.dataset.badgeImg;
      const badgeName = result.badge_awarded?.name || gameContainer.dataset.badgeName || 'เหรียญรางวัลเกียรติยศ';

      if (hasBadge) {
        if (feedbackBanner) {
          feedbackBanner.className = 'absolute top-0 inset-x-0 h-2.5 bg-gradient-to-r from-amber-400 via-yellow-400 to-sky-400';
        }
        if (feedbackIconBox) {
          feedbackIconBox.innerHTML = `
            <div class="relative flex flex-col items-center justify-center my-1">
              <div class="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl bg-gradient-to-tr from-amber-50 to-sky-50 border-2 border-amber-300 p-2.5 flex items-center justify-center shadow-xl shadow-amber-500/20 ring-4 ring-amber-100 animate-bounce">
                ${inlineBadgeSvg || `<img src="${badgeImgUrl}" alt="${badgeName}" class="w-full h-full object-contain filter drop-shadow-md" onerror="this.style.display='none'">`}
              </div>
              <div class="absolute -bottom-2 px-3 py-0.5 rounded-full bg-amber-500 text-white text-2xs font-black uppercase tracking-wider shadow-sm flex items-center gap-1">
                <span>★</span><span>BADGE UNLOCKED</span><span>★</span>
              </div>
            </div>
          `;
        }
        if (feedbackStatusBadge) {
          feedbackStatusBadge.className = 'inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs sm:text-sm font-black tracking-wide bg-amber-100 text-amber-900 border border-amber-300 shadow-2xs mt-2';
          feedbackStatusBadge.innerHTML = '<span>🏆</span><span>ยินดีด้วย! คุณได้รับเหรียญรางวัล (BADGE AWARDED!)</span>';
        }
      } else {
        const isAck = !!(result.is_acknowledgment || result.result_type === 'acknowledgment' || activityType === 'intro' || activityType === 'outcome');
        if (feedbackBanner) {
          feedbackBanner.className = isAck
            ? 'absolute top-0 inset-x-0 h-2.5 bg-gradient-to-r from-sky-400 via-teal-400 to-indigo-400'
            : 'absolute top-0 inset-x-0 h-2.5 bg-gradient-to-r from-emerald-500 via-teal-400 to-sky-400';
        }
        if (feedbackIconBox) {
          if (isAck) {
            feedbackIconBox.innerHTML = `
              <div class="w-18 h-18 sm:w-20 sm:h-20 rounded-full bg-gradient-to-tr from-sky-500 to-indigo-500 text-white flex items-center justify-center shadow-lg shadow-sky-500/30 ring-8 ring-sky-100 animate-pulse">
                <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            `;
          } else {
            feedbackIconBox.innerHTML = `
              <div class="w-18 h-18 sm:w-20 sm:h-20 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 text-white flex items-center justify-center shadow-lg shadow-emerald-500/30 ring-8 ring-emerald-100 animate-bounce">
                <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            `;
          }
        }
        if (feedbackStatusBadge) {
          if (isAck) {
            feedbackStatusBadge.className = 'inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs sm:text-sm font-bold tracking-wide bg-sky-100 text-sky-800 border border-sky-300 shadow-2xs';
            feedbackStatusBadge.innerHTML = '<span>ℹ️</span><span>รับทราบข้อมูล (NOTED / PROCEED)</span>';
          } else {
            feedbackStatusBadge.className = 'inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs sm:text-sm font-black tracking-wide bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs';
            feedbackStatusBadge.innerHTML = '<span>🎉</span><span>ถูกต้องยอดเยี่ยม! (EXCELLENT!)</span>';
          }
        }
      }

      if (feedbackActionBtn) {
        const nextLabel = result.is_mission_completed ? 'ดูการสะท้อนคิดปิดภารกิจ (View Debrief)' : 'ไปยังขั้นตอนถัดไป (Next Step)';
        feedbackActionBtn.innerHTML = `<span>${nextLabel}</span> <svg class="w-5 h-5 ml-1 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>`;
        feedbackActionBtn.className = 'w-full py-4 px-6 rounded-2xl font-black text-base text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-sky-600 hover:from-emerald-500 hover:via-teal-500 hover:to-sky-500 active:scale-[0.98] shadow-lg shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer touch-target';
        feedbackActionBtn.onclick = function () {
          if (result.is_mission_completed) {
            window.location.href = window.location.pathname;
          } else {
            window.location.reload();
          }
        };
      }

      if (!result.is_acknowledgment && result.result_type !== 'acknowledgment' && activityType !== 'intro' && activityType !== 'outcome') {
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

    function updateStepBadges() {
      const items = sequenceList.querySelectorAll('li[data-step-key]');
      items.forEach((item, index) => {
        const badge = item.querySelector('.step-order-badge');
        if (badge) {
          badge.textContent = index + 1;
        }
      });
    }

    // Scramble the cards initially so the activity doesn't start already in solved order
    const initialItems = Array.from(sequenceList.querySelectorAll('li[data-step-key]'));
    if (initialItems.length > 1) {
      const seed = parseInt(runId || '42', 10) * 101 + parseInt(activityId || '5', 10);
      let s = seed;
      function pseudoRandom() {
        s = (s * 9301 + 49297) % 233280;
        return s / 233280;
      }
      const shuffled = [...initialItems];
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(pseudoRandom() * (i + 1));
        const temp = shuffled[i];
        shuffled[i] = shuffled[j];
        shuffled[j] = temp;
      }
      let same = true;
      for (let i = 0; i < initialItems.length; i++) {
        if (initialItems[i] !== shuffled[i]) {
          same = false;
          break;
        }
      }
      if (same && shuffled.length > 1) {
        const first = shuffled[0];
        shuffled[0] = shuffled[1];
        shuffled[1] = first;
      }
      shuffled.forEach((el) => sequenceList.appendChild(el));
      updateStepBadges();
    }

    // 1. Initialize SortableJS for drag-and-drop
    if (window.Sortable) {
      new window.Sortable(sequenceList, {
        animation: 150,
        ghostClass: 'opacity-50',
        chosenClass: 'bg-sky-100',
        handle: '.drag-handle',
        onEnd: function () {
          updateStepBadges();
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
          updateStepBadges();
          item.focus();
          announce('เลื่อนขั้นตอนขึ้นแล้ว');
        }
      } else if (btn.dataset.action === 'move-down') {
        const next = item.nextElementSibling;
        if (next) {
          sequenceList.insertBefore(next, item);
          updateStepBadges();
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
      const loadingText = activityType === 'intro'
        ? 'กำลังเริ่มกิจกรรม...'
        : (activityType === 'outcome' ? 'กำลังไปยังขั้นตอนถัดไป...' : 'กำลังบันทึกคำตอบ...');
      submitBtn.innerHTML = `
        <span class="inline-flex items-center gap-2">
          <svg class="animate-spin h-4 w-4 text-white shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span>${loadingText}</span>
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

      if (activityType === 'intro' || activityType === 'outcome') {
        // Informational introduction or outcome transition steps:
        // Transition directly into the next step without an irrelevant "EXCELLENT!" quiz grading modal
        window.location.reload();
        return;
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
      } else if ((activityType === 'decision' || activityType === 'troubleshooting') && document.querySelector('input[name="choice"]')) {
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

  // Initialize interactive components based on activity type (only in active gameplay mode)
  if (!isReview) {
    if (activityType === 'sequence') {
      initSequence();
    } else if (
      activityType === 'clinical_cues' ||
      activityType === 'equipment_select' ||
      activityType === 'medication_check' ||
      activityType === 'safety_check' ||
      activityType === 'aftercare' ||
      activityType === 'troubleshooting' ||
      activityType === 'decision' ||
      document.querySelectorAll('.selection-card').length > 0
    ) {
      if (document.querySelectorAll('.selection-card').length > 0) {
        initSelection();
      }
    }
  }

  // Escape key closes modal
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && feedbackModal && !feedbackModal.classList.contains('hidden')) {
      closeFeedback();
    }
  });
})();
