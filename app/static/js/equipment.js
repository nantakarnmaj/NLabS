/**
 * BreathQuest Equipment Preparation Station
 * Handles picture-name card matching, basket packing, and clinical verification.
 * Adheres strictly to Content Security Policy (CSP script-src 'self' without inline scripts).
 */

(function () {
  'use strict';

  // Read server configuration from the JSON data block
  const configElement = document.getElementById('equipment-data');
  if (!configElement) {
    console.error('[BQ] #equipment-data element not found');
    return;
  }

  let config;
  try {
    config = JSON.parse(configElement.textContent);
  } catch (err) {
    console.error('[BQ] Failed to parse #equipment-data JSON:', err);
    return;
  }

  const activeBasketId = config.activeBasketId;
  const catalogData = config.catalog || {};
  const totalRequired = config.totalRequired || 0;
  const verifyUrl = config.verifyUrl || '/equipment-station/verify';

  // Selection & gameplay state
  let selectedPictureId = null;
  let selectedNameId = null;
  const pairedItemIds = new Set();
  const packedInBasketIds = new Set();
  let lastTapTimestamp = 0;

  // ===== Selection Handlers =====

  function selectPictureCard(itemId) {
    const now = Date.now();
    if (now - lastTapTimestamp < 120) return;
    lastTapTimestamp = now;

    console.log('[BQ] selectPictureCard', itemId);

    if (pairedItemIds.has(itemId)) {
      toggleBasketPacking(itemId);
      return;
    }

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
      updateStatusHint('📸 เลือกรูป: <strong class="text-sky-700">' + nm + '</strong> แล้ว 👉 <span class="text-[#0284c7] font-bold">แตะชื่ออุปกรณ์ทางขวา</span>ที่ตรงกัน');
    }
  }

  function selectNameCard(itemId) {
    const now = Date.now();
    if (now - lastTapTimestamp < 120) return;
    lastTapTimestamp = now;

    console.log('[BQ] selectNameCard', itemId);

    if (pairedItemIds.has(itemId)) {
      toggleBasketPacking(itemId);
      return;
    }

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
      updateStatusHint('🏷️ เลือกชื่อ: <strong class="text-sky-700">' + nm + '</strong> แล้ว 👉 <span class="text-[#0284c7] font-bold">แตะรูปถ่ายทางซ้าย</span>ที่ตรงกัน');
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
    console.log('[BQ] check match:', selectedPictureId, '===', selectedNameId, '?', selectedPictureId === selectedNameId);

    if (selectedPictureId === selectedNameId) {
      handleSuccessfulMatch(selectedPictureId);
    } else {
      handleFailedMatch();
    }
  }

  function handleSuccessfulMatch(itemId) {
    const item = catalogData[itemId];
    console.log('[BQ] SUCCESS match:', itemId);

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
    updateStatusHint('🎉 <strong class="text-emerald-700">ยอดเยี่ยม! จับคู่ ' + (item ? item.name_th : itemId) + ' ถูกต้อง!</strong> บรรจุใส่ตะกร้าหัตถการเรียบร้อยแล้ว 🧺');
  }

  function handleFailedMatch() {
    const wrongPicId = selectedPictureId;
    const wrongNameId = selectedNameId;
    const picItem = catalogData[wrongPicId];
    console.log('[BQ] MISMATCH pic:', wrongPicId, 'name:', wrongNameId);

    updateStatusHint('❌ <span class="text-rose-600 font-bold">ยังไม่ตรงกัน:</span> กำลังเลือกรูป <strong>' + (picItem ? picItem.name_th : '') + '</strong> (กรอบฟ้า) 👉 แตะชื่ออุปกรณ์ที่ตรงกันอีกครั้ง');

    const nameCard = document.querySelector('.name-card[data-item-id="' + wrongNameId + '"]');
    if (nameCard) {
      nameCard.classList.add('animate-shake');
      nameCard.style.cssText += 'border-color:#f43f5e!important;box-shadow:0 0 0 4px rgba(244,63,94,.45)!important;';
    }

    setTimeout(function () {
      if (nameCard) {
        nameCard.classList.remove('animate-shake', 'is-selected');
        nameCard.removeAttribute('data-selected');
        nameCard.style.borderColor = '';
        nameCard.style.boxShadow = '';
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
      updateStatusHint('🧺 นำ <strong>' + nm + '</strong> ออกจากตะกร้าแล้ว');
    } else {
      packItemIntoBasket(itemId);
      updateStatusHint('🧺 นำ <strong>' + nm + '</strong> ใส่ตะกร้าเรียบร้อย!');
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
        '<img src="/static/' + item.image + '?v=20261014c" class="w-10 h-10 object-contain rounded-lg bg-slate-50 border border-slate-200 shrink-0 p-1" alt="' + item.name_th + '">' +
        '<div class="min-w-0">' +
          '<div class="text-xs font-black text-slate-900 truncate">' + item.name_th + '</div>' +
          '<div class="text-2xs font-mono text-indigo-600 truncate">' + item.name_en + '</div>' +
        '</div>' +
      '</div>';

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'w-7 h-7 rounded-lg bg-slate-100 hover:bg-rose-100 text-slate-400 hover:text-rose-600 flex items-center justify-center text-xs font-bold transition shrink-0';
    removeBtn.title = 'หยิบออกจากตะกร้า';
    removeBtn.textContent = '✕';
    removeBtn.addEventListener('click', function () {
      removeFromBasket(item.id);
    });

    row.appendChild(removeBtn);
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
      '<img src="/static/' + item.image + '?v=20261014c" class="w-7 h-7 object-contain rounded-md bg-slate-50 border border-slate-100" alt="' + item.name_th + '">' +
      '<span class="text-xs font-bold text-slate-800">' + item.name_th + '</span>';

    const packBtn = document.createElement('button');
    packBtn.type = 'button';
    packBtn.className = 'px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-2xs transition';
    packBtn.title = 'หยิบใส่ตะกร้าหัตถการ';
    packBtn.textContent = 'หยิบใส่ตะกร้า 🧺';
    packBtn.addEventListener('click', function () {
      packItemIntoBasket(item.id);
    });

    chip.appendChild(packBtn);
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

  function updateStatusHint(msg) {
    const hint = document.getElementById('pairing-status-hint');
    if (hint) hint.innerHTML = msg;
  }

  // ===== Basket Verification & Feedback Modal =====

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
      const result = await res.json();
      displayFeedbackModal(result);
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
        box.innerHTML = '<div class="font-bold flex items-center gap-2"><span>✓</span><span>' + result.feedback + '</span></div>';
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
        box.innerHTML = '<div>' + result.feedback + '</div>';
      }
    }
    modal.classList.remove('hidden');
  }

  function closeFeedbackModal() {
    const modal = document.getElementById('feedback-modal');
    if (modal) modal.classList.add('hidden');
  }

  // ===== Event Listeners Initialization (CSP Compliant via addEventListener) =====

  function initEquipmentStation() {
    // 1. Picture card buttons
    document.querySelectorAll('.pic-card').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const id = btn.getAttribute('data-item-id');
        if (id) selectPictureCard(id);
      });
    });

    // 2. Name card buttons
    document.querySelectorAll('.name-card').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const id = btn.getAttribute('data-item-id');
        if (id) selectNameCard(id);
      });
    });

    // 3. Reset button
    const resetBtn = document.getElementById('btn-reset-pairs');
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        if (confirm('ต้องการรีเซ็ตการจับคู่ของตะกร้านี้ทั้งหมดหรือไม่?')) {
          window.location.reload();
        }
      });
    }

    // 4. Verify basket button
    const verifyBtn = document.getElementById('btn-verify-basket');
    if (verifyBtn) {
      verifyBtn.addEventListener('click', submitBasketVerification);
    }

    // 5. Close feedback modal buttons & backdrop
    const closeBtn = document.getElementById('btn-close-modal');
    if (closeBtn) {
      closeBtn.addEventListener('click', closeFeedbackModal);
    }
    const feedbackModal = document.getElementById('feedback-modal');
    if (feedbackModal) {
      feedbackModal.addEventListener('click', function (e) {
        if (e.target === feedbackModal) closeFeedbackModal();
      });
    }
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeFeedbackModal();
    });

    console.log('[BQ] Equipment station initialized successfully under CSP. Catalog items:', Object.keys(catalogData).length);
  }

  // Run initialization when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEquipmentStation);
  } else {
    initEquipmentStation();
  }

})();
