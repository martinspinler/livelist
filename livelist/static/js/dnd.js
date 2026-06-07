function initDragAndDrop(s, handle_drag_and_drop) {
    const livelist = document.querySelector("#livelist-items");
    const state = s;

    let draggedItem = null;
    let draggedItemId = null;
    let isDragging = false;
    let startClientY = 0;
    let startClientX = 0;
    let currentClientX = 0;
    let currentClientY = 0;
    let lastTargetItem = null;
    let lastBefore = null;

    // Minimum distance in px before a pointer-down is considered a drag
    const DRAG_THRESHOLD = 5;

    // Auto-scroll configuration
    const AUTO_SCROLL_ZONE = 100;   // px from viewport edge to trigger scrolling
    const AUTO_SCROLL_SPEED = 1000; // base px/sec (roughly 3 items/sec at ~60px/item)

    let scrollAnimationId = null;

    livelist.addEventListener('pointerdown', onPointerDown);

    function onPointerDown(e) {
        // Only allow drag in Move mode
        if (!state.moveMode) return;

        const handle = e.target.closest('.drag-handle');
        if (!handle) return;

        const item = handle.closest('.livelist-item, .livelist-break');
        if (!item) return;

        draggedItem = item;
        draggedItemId = item.dataset.itemId;
        isDragging = false;
        startClientX = e.clientX;
        startClientY = e.clientY;
        currentClientX = e.clientX;
        currentClientY = e.clientY;

        document.addEventListener('pointermove', onPointerMove);
        document.addEventListener('pointerup', onPointerUp);
        document.addEventListener('pointercancel', onPointerUp);
    }

    function onPointerMove(e) {
        if (!draggedItem) return;

        currentClientX = e.clientX;
        currentClientY = e.clientY;

        const dx = e.clientX - startClientX;
        const dy = e.clientY - startClientY;

        // Wait until the pointer has moved beyond the threshold before
        // committing to a drag – this avoids accidental drags on clicks.
        if (!isDragging) {
            if (Math.abs(dx) < DRAG_THRESHOLD && Math.abs(dy) < DRAG_THRESHOLD) {
                return;
            }
            isDragging = true;
            draggedItem.classList.add('dragging');

            livelist.setPointerCapture(e.pointerId);
        }

        updateDragVisuals();
        checkAutoScroll();
    }

    /**
     * Recalculate which livelist-item is under the pointer and apply
     * the drag-before / drag-after CSS classes.
     *
     * Skips re-rendering when the insertion point hasn't changed — this
     * prevents wobble at item boundaries where "after A" and "before B"
     * represent the same gap.
     */
    function updateDragVisuals() {
        draggedItem.style.display = 'none';
        const targetEl = document.elementFromPoint(currentClientX, currentClientY);
        draggedItem.style.display = '';

        if (!targetEl) {
            clearDragClasses();
            lastTargetItem = null;
            lastBefore = null;
            return;
        }

        const targetItem = targetEl.closest('.livelist-item, .livelist-break');
        if (!targetItem || targetItem === draggedItem) {
            clearDragClasses();
            lastTargetItem = null;
            lastBefore = null;
            return;
        }

        const rect = targetItem.getBoundingClientRect();
        let before = currentClientY < rect.top + rect.height / 2;

        // Set 1 is the virtual first header — nothing can go above it,
        // so force drag-after (insert as first song in the playlist).
        if (before && targetItem.dataset.setKey) {
            before = false;
        }

        // Same insertion point as last time — skip re-render
        if (targetItem === lastTargetItem && before === lastBefore) return;

        // Check for equivalent insertion point (after A == before A.nextElementSibling)
        if (lastTargetItem !== null && lastBefore !== null) {
            if (before && !lastBefore && lastTargetItem.nextElementSibling === targetItem) return;
            if (!before && lastBefore && targetItem.nextElementSibling === lastTargetItem) return;
        }

        clearDragClasses();

        if (before) {
            targetItem.classList.add('drag-before');
        } else {
            targetItem.classList.add('drag-after');
        }

        lastTargetItem = targetItem;
        lastBefore = before;
    }

    // ---- Auto-scroll ----

    /**
     * Return the viewport Y coordinate that marks the top of the area
     * where list items are visible (just below any sticky headers).
     */
    function getScrollAreaTop() {
        const nav = document.querySelector('nav.sticky-top');
        if (nav) {
            return nav.getBoundingClientRect().bottom;
        }
        return 0;
    }

    function checkAutoScroll() {
        if (!isDragging || !draggedItem) {
            stopAutoScroll();
            return;
        }

        const topEdge = getScrollAreaTop();
        const bottomEdge = window.innerHeight;

        const nearTop = currentClientY >= topEdge && currentClientY < topEdge + AUTO_SCROLL_ZONE;
        const nearBottom = currentClientY > bottomEdge - AUTO_SCROLL_ZONE;

        if (nearTop || nearBottom) {
            startAutoScroll();
        } else {
            stopAutoScroll();
        }
    }

    function startAutoScroll() {
        if (scrollAnimationId !== null) return; // already running

        let lastTime = null;

        function step(timestamp) {
            if (!isDragging || !draggedItem) {
                stopAutoScroll();
                return;
            }

            if (!lastTime) lastTime = timestamp;
            const delta = Math.min((timestamp - lastTime) / 1000, 0.1);
            lastTime = timestamp;

            const topEdge = getScrollAreaTop();
            const bottomEdge = window.innerHeight;

            let scrolled = false;

            if (currentClientY >= topEdge && currentClientY < topEdge + AUTO_SCROLL_ZONE) {
                const intensity = 1 - (currentClientY - topEdge) / AUTO_SCROLL_ZONE;
                const amount = -AUTO_SCROLL_SPEED * delta * intensity;
                window.scrollBy({ top: amount, behavior: 'instant' });
                scrolled = true;
            } else if (currentClientY > bottomEdge - AUTO_SCROLL_ZONE) {
                const intensity = 1 - (bottomEdge - currentClientY) / AUTO_SCROLL_ZONE;
                const amount = AUTO_SCROLL_SPEED * delta * intensity;
                window.scrollBy({ top: amount, behavior: 'instant' });
                scrolled = true;
            }

            if (scrolled) {
                // Content shifted under the stationary pointer – refresh highlight
                updateDragVisuals();
            }

            if (!scrolled) {
                stopAutoScroll();
                return;
            }

            scrollAnimationId = requestAnimationFrame(step);
        }

        scrollAnimationId = requestAnimationFrame(step);
    }

    function stopAutoScroll() {
        if (scrollAnimationId !== null) {
            cancelAnimationFrame(scrollAnimationId);
            scrollAnimationId = null;
        }
    }

    // ---- End auto-scroll ----

    function onPointerUp(e) {
        document.removeEventListener('pointermove', onPointerMove);
        document.removeEventListener('pointerup', onPointerUp);
        document.removeEventListener('pointercancel', onPointerUp);

        stopAutoScroll();

        if (isDragging) {
            try {
                livelist.releasePointerCapture(e.pointerId);
            } catch (_) {
                // May already be released
            }
        }

        if (!draggedItem) return;

        if (isDragging) {
            draggedItem.style.display = 'none';
            const targetEl = document.elementFromPoint(e.clientX, e.clientY);
            draggedItem.style.display = '';

            const targetItem = targetEl ? targetEl.closest('.livelist-item, .livelist-break') : null;

            if (targetItem && draggedItem !== targetItem) {
                const draggedPliId = draggedItem.dataset.itemId;
                let targetPliId = targetItem.dataset.itemId;

                const rect = targetItem.getBoundingClientRect();
                let before = e.clientY < rect.top + rect.height / 2;

                // Set 1 is a virtual header with no itemId — resolve to the
                // first real item in the list so items can be moved to the top.
                if (!targetPliId && targetItem.dataset.setKey) {
                    const firstItem = livelist.querySelector('.livelist-item[data-item-id]');
                    if (firstItem) {
                        targetPliId = firstItem.dataset.itemId;
                        before = true;
                    }
                }

                if (targetPliId) {
                    const msg = {
                        moved_ids: [parseInt(draggedPliId)],
                        target_id: parseInt(targetPliId),
                        before: before,
                        playlist_id: state.currentPlaylist,
                    };
                    handle_drag_and_drop(msg);
                }
            }
        }

        cleanupDrag();
    }

    function clearDragClasses() {
        livelist.querySelectorAll('.livelist-item, .livelist-break').forEach(item => {
            item.classList.remove('drag-before', 'drag-after');
        });
    }

    function cleanupDrag() {
        stopAutoScroll();

        if (draggedItem) {
            draggedItem.classList.remove('dragging', 'disabled', 'd-none');
            draggedItem.style.display = '';
        }

        clearDragClasses();

        draggedItem = null;
        draggedItemId = null;
        isDragging = false;
        lastTargetItem = null;
        lastBefore = null;
    }
}
