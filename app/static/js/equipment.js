/**
 * BreathQuest Equipment Preparation Station
 * Handles picture-name card matching, basket packing, and clinical verification.
 * Adheres strictly to Content Security Policy (CSP script-src 'self' without inline scripts).
 */

(function () {
  'use strict';

  let config = null;
  let activeBasketId = null;
  let catalogData = {};
  let totalRequired = 0;
  let verifyUrl = '/equipment-station/verify';

  // Selection & gameplay state
  let selectedPictureId = null;
  let selectedNameId = null;
  const pairedItemIds = new Set();
  const packedInBasketIds = new Set();
  let initialized = false;

  function loadConfig() {
    const configElement = document.getElementById('equipment-data');
    if (!configElement) return false;
    try {
      config = JSON.parse(configElement.textContent);
      activeBasketId = config.activeBasketId;
      catalogData = config.catalog || {};
      totalRequired = config.totalRequired || 0;
      verifyUrl = config.verifyUrl || '/equipment-station/verify';
      return true;
    } catch (err) {
      console.error('[BQ] Failed to parse #equipment-data JSON:', err);
      return false;
    }
  }

  // ===== Selection Handlers =====

  function selectPictureCard(itemId) {
    console.log('[BQ] selectPictureCard:', itemId);

    // If already paired, clicking it toggles in/out of basket
    if (pairedItemIds.has(itemId)) {
      toggleBasketPacking(itemId);
      return;
    }

    // Toggle off if re-clicking same picture
    if (selectedPictureId === itemId) {
      selectedPictureId = null;
      applySelectionStyle();
      updateStatusHint('แตะเลือก <strong>รูปถ่ายอุปกรณ์</strong> หรือ <strong>ชื่ออุปกรณ์</strong> เพื่อเริ่มจับคู่');
      return;
    }

    selectedPictureId = itemId;
    applySelectionStyle();

    if (selectedNameId) {
      checkMatchAttempt();
    } else {
      const nm = catalogData[itemId] ? catalogData[itemId].name_th : itemId;
      updateStatusHint('📸 เลือกรูป: <strong class="text-sky-700">' + escapeHtml(nm) + '</strong> แล้ว 👉 <span class="text-[#0284c7] font-bold">แตะชื่ออุปกรณ์ทางขวา</span>ที่ตรงกัน');
    }
  }

  function selectNameCard(itemId) {
    console.log('[BQ] selectNameCard:', itemId);

    // If already paired, clicking it toggles in/out of basket
    if (pairedItemIds.has(itemId)) {
      toggleBasketPacking(itemId);
      return;
    }

    // Toggle off if re-clicking same name
    if (selectedNameId === itemId) {
      selectedNameId = null;
      applySelectionStyle();
      updateStatusHint('แตะเลือก <strong>รูปถ่ายอุปกรณ์</strong> หรือ <strong>ชื่ออุปกรณ์</strong> เพื่อเริ่มจับคู่');
      return;
    }

    selectedNameId = itemId;
    applySelectionStyle();

    if (selectedPictureId) {
      checkMatchAttempt();
    } else {
      const nm = catalogData[itemId] ? catalogData[itemId].name_th : itemId;
      updateStatusHint('🏷️ เลือกชื่อ: <strong class="text-sky-700">' + escapeHtml(nm) + '</strong> แล้ว 👉 <span class="text-[#0284c7] font-bold">แตะรูปถ่ายทางซ้าย</span>ที่ตรงกัน');
    }
  }

  function applySelectionStyle() {
    document.querySelectorAll('.pic-card').forEach(function (c) {
      const id = c.getAttribute('data-item-id');
      const sel = (id === selectedPictureId);
      c.classList.toggle('is-selected', sel);
      if (sel) {
        c.setAttribute('data-selected', 'true');
      } else {
        c.removeAttribute('data-selected');
      }

      const badge = c.querySelector('.pic-selected-badge');
      if (badge) {
        if (sel) badge.classList.remove('hidden');
        else badge.classList.add('hidden');
      }
    });

    document.querySelectorAll('.name-card').forEach(function (c) {
      const id = c.getAttribute('data-item-id');
      const sel = (id === selectedNameId);
      c.classList.toggle('is-selected', sel);
      if (sel) {
        c.setAttribute('data-selected', 'true');
      } else {
        c.removeAttribute('data-selected');
      }

      const status = c.querySelector('.name-selected-status');
      if (status) {
        if (sel) status.classList.remove('hidden');
        else status.classList.add('hidden');
      }
    });
  }

  // ===== Matching Logic =====

  function checkMatchAttempt() {
    if (!selectedPictureId || !selectedNameId) return;
    console.log('[BQ] Checking match:', selectedPictureId, '===', selectedNameId);

    if (selectedPictureId === selectedNameId) {
      handleSuccessfulMatch(selectedPictureId);
    } else {
      handleFailedMatch();
    }
  }

  function handleSuccessfulMatch(itemId) {
    const item = catalogData[itemId];
    console.log('[BQ] MATCH SUCCESS:', itemId);

    pairedItemIds.add(itemId);

    const picCard = document.querySelector('.pic-card[data-item-id="' + itemId + '"]');
    if (picCard) {
      picCard.classList.remove('is-selected');
      picCard.removeAttribute('data-selected');
      picCard.classList.add('is-paired');
      const selBadge = picCard.querySelector('.pic-selected-badge');
      if (selBadge) selBadge.classList.add('hidden');
      const pairBadge = picCard.querySelector('.pic-paired-badge');
      if (pairBadge) pairBadge.classList.remove('hidden');
    }

    const nameCard = document.querySelector('.name-card[data-item-id="' + itemId + '"]');
    if (nameCard) {
      nameCard.classList.remove('is-selected');
      nameCard.removeAttribute('data-selected');
      nameCard.classList.add('is-paired');
      const selStatus = nameCard.querySelector('.name-selected-status');
      if (selStatus) selStatus.classList.add('hidden');
      const pairStatus = nameCard.querySelector('.name-paired-status');
      if (pairStatus) pairStatus.classList.remove('hidden');
    }

    selectedPictureId = null;
    selectedNameId = null;
    applySelectionStyle();

    packItemIntoBasket(itemId);
    updatePairedCardBadges(itemId);
    updateRemainingCounters();
    updateStatusHint('🎉 <strong class="text-emerald-700">ยอดเยี่ยม! จับคู่ ' + escapeHtml(item ? item.name_th : itemId) + ' ถูกต้อง!</strong> บรรจุใส่ตะกร้าหัตถการเรียบร้อยแล้ว 🧺');
  }

  function handleFailedMatch() {
    const wrongPicId = selectedPictureId;
    const wrongNameId = selectedNameId;
    const picItem = catalogData[wrongPicId];
    console.log('[BQ] MISMATCH pic:', wrongPicId, 'name:', wrongNameId);

    updateStatusHint('❌ <span class="text-rose-600 font-bold">ยังไม่ตรงกัน:</span> กำลังเลือกรูป <strong>' + (picItem ? escapeHtml(picItem.name_th) : '') + '</strong> (กรอบฟ้า) 👉 แตะชื่ออุปกรณ์ที่ตรงกันอีกครั้ง');

    const nameCard = document.querySelector('.name-card[data-item-id="' + wrongNameId + '"]');
    if (nameCard) {
      nameCard.classList.add('animate-shake', 'is-mismatch');
    }

    setTimeout(function () {
      if (nameCard) {
        nameCard.classList.remove('animate-shake', 'is-mismatch', 'is-selected');
        nameCard.removeAttribute('data-selected');
        const ns = nameCard.querySelector('.name-selected-status');
        if (ns) ns.classList.add('hidden');
      }
      // Picture card stays selected in blue!
      selectedNameId = null;
    }, 700);
  }

  // ===== Basket & Staging Packing =====

  function toggleBasketPacking(itemId) {
    const item = catalogData[itemId];
    const nm = item ? item.name_th : itemId;
    if (packedInBasketIds.has(itemId)) {
      removeFromBasket(itemId);
      updateStatusHint('🧺 นำ <strong>' + escapeHtml(nm) + '</strong> ออกจากตะกร้าแล้ว');
    } else {
      packItemIntoBasket(itemId);
      updateStatusHint('🧺 นำ <strong>' + escapeHtml(nm) + '</strong> ใส่ตะกร้าเรียบร้อย!');
    }
    updatePairedCardBadges(itemId);
  }

  function updatePairedCardBadges(itemId) {
    const isPacked = packedInBasketIds.has(itemId);
    const picCard = document.querySelector('.pic-card[data-item-id="' + itemId + '"]');
    const nameCard = document.querySelector('.name-card[data-item-id="' + itemId + '"]');
    if (picCard) {
      const badge = picCard.querySelector('.pic-paired-badge');
      if (badge) {
        badge.innerHTML =
          '<span class="text-2xl">' + (isPacked ? '✓' : '📦') + '</span>' +
          '<span class="text-xs font-black">จับคู่ถูกต้อง!</span>' +
          '<span class="text-3xs ' + (isPacked ? 'bg-white text-emerald-800' : 'bg-amber-100 text-amber-900') + ' font-bold px-2 py-0.5 rounded-full shadow-2xs">' +
            (isPacked ? '🧺 บรรจุในตะกร้าแล้ว' : '📦 อยู่นอกตะกร้า (แตะใส่)') +
          '</span>';
      }
    }
    if (nameCard) {
      const status = nameCard.querySelector('.name-paired-status');
      if (status) {
        status.innerHTML = '<span>✓ จับคู่สำเร็จ (' + (isPacked ? 'อยู่ในตะกร้า 🧺' : 'อยู่นอกตะกร้า 📦') + ')</span>';
      }
    }
  }

  function packItemIntoBasket(itemId) {
    if (packedInBasketIds.has(itemId)) return;
    packedInBasketIds.add(itemId);
    const item = catalogData[itemId] || { id: itemId, name_th: itemId, name_en: itemId, image: '' };

    const stagedChip = document.getElementById('staged-' + itemId);
    if (stagedChip) stagedChip.remove();

    const shelf = document.getElementById('staging-shelf');
    if (shelf && shelf.querySelectorAll('[id^="staged-"]').length === 0) {
      const em = document.getElementById('staging-empty-msg');
      if (em) em.classList.remove('hidden');
    }

    const basket = document.getElementById('procedure-basket');
    const placeholder = document.getElementById('basket-empty-placeholder');
    if (placeholder) placeholder.classList.add('hidden');

    const row = document.createElement('div');
    row.id = 'basket-item-' + item.id;
    row.className = 'p-3 rounded-xl bg-white border border-indigo-200 shadow-2xs flex items-center justify-between gap-3';
    row.innerHTML =
      '<div class="flex items-center gap-3 min-w-0">' +
        '<img src="/static/' + escapeHtml(item.image) + '?v=20261014c" class="w-10 h-10 object-contain rounded-lg bg-slate-50 border border-slate-200 shrink-0 p-1" alt="' + escapeHtml(item.name_th) + '">' +
        '<div class="min-w-0">' +
          '<div class="text-xs font-black text-slate-900 truncate">' + escapeHtml(item.name_th) + '</div>' +
          '<div class="text-2xs font-mono text-indigo-600 truncate">' + escapeHtml(item.name_en) + '</div>' +
        '</div>' +
      '</div>' +
      '<button type="button" class="btn-remove-basket-item w-7 h-7 rounded-lg bg-slate-100 hover:bg-rose-100 text-slate-400 hover:text-rose-600 flex items-center justify-center text-xs font-bold transition shrink-0" data-item-id="' + escapeHtml(item.id) + '" title="หยิบออกจากตะกร้า">' +
        '✕' +
      '</button>';

    basket.appendChild(row);
    updateBasketCounters();
  }

  function removeFromBasket(itemId) {
    packedInBasketIds.delete(itemId);
    const item = catalogData[itemId];
    const row = document.getElementById('basket-item-' + itemId);
    if (row) row.remove();

    const basket = document.getElementById('procedure-basket');
    if (basket && basket.querySelectorAll('[id^="basket-item-"]').length === 0) {
      const ph = document.getElementById('basket-empty-placeholder');
      if (ph) ph.classList.remove('hidden');
    }

    if (item) addToStagingShelf(item);
    updateBasketCounters();
    updatePairedCardBadges(itemId);
  }

  function addToStagingShelf(item) {
    const shelf = document.getElementById('staging-shelf');
    const em = document.getElementById('staging-empty-msg');
    if (em) em.classList.add('hidden');

    const chip = document.createElement('div');
    chip.id = 'staged-' + item.id;
    chip.className = 'inline-flex items-center gap-2 p-2 rounded-xl bg-white border border-emerald-300 shadow-2xs';
    chip.innerHTML =
      '<img src="/static/' + escapeHtml(item.image) + '?v=20261014c" class="w-7 h-7 object-contain rounded-md bg-slate-50 border border-slate-100" alt="' + escapeHtml(item.name_th) + '">' +
      '<span class="text-xs font-bold text-slate-800">' + escapeHtml(item.name_th) + '</span>' +
      '<button type="button" class="btn-pack-staged-item px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-2xs transition" data-item-id="' + escapeHtml(item.id) + '" title="หยิบใส่ตะกร้าหัตถการ">' +
        'หยิบใส่ตะกร้า 🧺' +
      '</button>';

    shelf.appendChild(chip);
  }

  function updateRemainingCounters() {
    const total = document.querySelectorAll('.pic-card').length;
    const remaining = total - pairedItemIds.size;
    const pl = document.getElementById('pic-remaining-label');
    const nl = document.getElementById('name-remaining-label');
    if (pl) pl.textContent = 'เหลือ ' + remaining + ' ภาพ';
    if (nl) nl.textContent = 'เหลือ ' + remaining + ' รายการ';
  }

  function updateBasketCounters() {
    const count = packedInBasketIds.size;
    const counter = document.getElementById('basket-counter');
    const pill = document.getElementById('tray-count-pill');
    const badge = document.getElementById('mobile-basket-badge');
    if (counter) counter.textContent = count + ' / ' + totalRequired;
    if (pill) pill.textContent = count + ' รายการ';
    if (badge) badge.textContent = count + '/' + totalRequired;
  }

  function updateStatusHint(html) {
    const hint = document.getElementById('pairing-status-hint');
    if (hint) hint.innerHTML = html;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // ===== Verification & Modal =====

  async function submitBasketVerification() {
    if (packedInBasketIds.size === 0) {
      alert('กรุณาจับคู่และหยิบอุปกรณ์ใส่ตะกร้าอย่างน้อย 1 ชิ้น ก่อนตรวจความถูกต้องครับ');
      return;
    }

    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

    try {
      const res = await fetch(verifyUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          basket_id: activeBasketId,
          packed_ids: Array.from(packedInBasketIds),
        }),
      });
      const data = await res.json();
      displayFeedbackModal(data);
    } catch (err) {
      console.error('[BQ] Verification failed:', err);
      alert('เกิดข้อผิดพลาดในการตรวจสอบ โปรดลองอีกครั้ง');
    }
  }

  function displayFeedbackModal(result) {
    const modal = document.getElementById('feedback-modal');
    const iconC = document.getElementById('modal-icon-container');
    const title = document.getElementById('modal-title');
    const subtitle = document.getElementById('modal-subtitle');
    const box = document.getElementById('modal-feedback-box');
    if (!modal) return;

    if (result.is_complete) {
      if (iconC) {
        iconC.className = 'w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center text-2xl shrink-0';
        iconC.textContent = '🏆';
      }
      if (title) title.textContent = 'จัดตะกร้าหัตถการถูกต้องสมบูรณ์!';
      if (subtitle) subtitle.textContent = 'ความแม่นยำทางคลินิก 100% (First-Class Readiness)';
      if (box) {
        box.className = 'p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-sm leading-relaxed space-y-2';
        box.innerHTML = '<div class="font-bold flex items-center gap-2"><span>✓</span><span>' + escapeHtml(result.feedback) + '</span></div>';
      }
    } else {
      if (iconC) {
        iconC.className = 'w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center text-2xl shrink-0';
        iconC.textContent = '⚠️';
      }
      if (title) title.textContent = 'ยังจัดอุปกรณ์ไม่ครบถ้วน / มีสิ่งแปลกปลอม';
      if (subtitle) subtitle.textContent = 'คะแนนความพร้อม: ' + result.score_percent + '% (ใส่อุปกรณ์จำเป็น ' + result.correct_count + '/' + result.total_required + ')';
      if (box) {
        box.className = 'p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-950 text-sm leading-relaxed space-y-2';
        box.innerHTML = '<div>' + escapeHtml(result.feedback) + '</div>';
      }
    }
    modal.classList.remove('hidden');
  }

  function closeFeedbackModal() {
    const modal = document.getElementById('feedback-modal');
    if (modal) modal.classList.add('hidden');
  }

  // ===== Global Event Delegation (CSP Compliant & Device-Agnostic) =====

  function handleGlobalClick(e) {
    // 1. Picture card clicked
    const picCard = e.target.closest('.pic-card');
    if (picCard) {
      e.preventDefault();
      const id = picCard.getAttribute('data-item-id');
      if (id) selectPictureCard(id);
      return;
    }

    // 2. Name card clicked
    const nameCard = e.target.closest('.name-card');
    if (nameCard) {
      e.preventDefault();
      const id = nameCard.getAttribute('data-item-id');
      if (id) selectNameCard(id);
      return;
    }

    // 3. Reset pairs button
    const resetBtn = e.target.closest('#btn-reset-pairs');
    if (resetBtn) {
      e.preventDefault();
      if (confirm('ต้องการรีเซ็ตการจับคู่ของตะกร้านี้ทั้งหมดหรือไม่?')) {
        window.location.reload();
      }
      return;
    }

    // 4. Verify basket button
    const verifyBtn = e.target.closest('#btn-verify-basket');
    if (verifyBtn) {
      e.preventDefault();
      submitBasketVerification();
      return;
    }

    // 5. Close feedback modal button
    const closeBtn = e.target.closest('#btn-close-modal');
    if (closeBtn) {
      e.preventDefault();
      closeFeedbackModal();
      return;
    }

    // 6. Modal backdrop click
    const feedbackModal = document.getElementById('feedback-modal');
    if (feedbackModal && e.target === feedbackModal) {
      closeFeedbackModal();
      return;
    }

    // 7. Remove item from basket button
    const removeBtn = e.target.closest('.btn-remove-basket-item');
    if (removeBtn) {
      e.preventDefault();
      const id = removeBtn.getAttribute('data-item-id');
      if (id) removeFromBasket(id);
      return;
    }

    // 8. Pack staged item into basket button
    const packBtn = e.target.closest('.btn-pack-staged-item');
    if (packBtn) {
      e.preventDefault();
      const id = packBtn.getAttribute('data-item-id');
      if (id) packItemIntoBasket(id);
      return;
    }
  }

  // ===== Initialization Routine =====

  function initEquipmentStation() {
    if (initialized) return;

    if (!loadConfig()) {
      // Retry if DOM elements are still being parsed
      setTimeout(initEquipmentStation, 50);
      return;
    }

    initialized = true;

    // Attach global click handler via delegation
    document.addEventListener('click', handleGlobalClick);

    // Escape key closes modal
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeFeedbackModal();
    });

    // Initial counter setup
    updateRemainingCounters();
    updateBasketCounters();

    console.log('[BQ] Equipment station initialized successfully under CSP. Catalog items:', Object.keys(catalogData).length);
  }

  // Execute initialization cleanly across all loading scenarios
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEquipmentStation);
  } else {
    initEquipmentStation();
  }
  window.addEventListener('load', initEquipmentStation);

})();
