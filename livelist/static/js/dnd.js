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

        const item = handle.closest('.livelist-item');
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
     * the drag-over / drag-before / drag-after CSS classes.
     */
    function updateDragVisuals() {
        draggedItem.style.display = 'none';
        const targetEl = document.elementFromPoint(currentClientX, currentClientY);
        draggedItem.style.display = '';

        clearDragClasses();

        if (!targetEl) return;

        const targetItem = targetEl.closest('.livelist-item');
        if (!targetItem || targetItem === draggedItem) return;

        targetItem.classList.add('drag-over');

        const rect = targetItem.getBoundingClientRect();
        const before = currentClientY < rect.top + rect.height / 2;

        if (before) {
            targetItem.classList.add('drag-before');
            targetItem.classList.remove('drag-after');
        } else {
            targetItem.classList.add('drag-after');
            targetItem.classList.remove('drag-before');
        }
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

            const targetItem = targetEl ? targetEl.closest('.livelist-item') : null;

            if (targetItem && draggedItem !== targetItem) {
                const draggedPliId = draggedItem.dataset.itemId;
                const targetPliId = targetItem.dataset.itemId;

                const rect = targetItem.getBoundingClientRect();
                const before = e.clientY < rect.top + rect.height / 2;

                const msg = {
                    moved_ids: [parseInt(draggedPliId)],
                    target_id: parseInt(targetPliId),
                    before: before,
                    playlist_id: state.currentPlaylist,
                };

                handle_drag_and_drop(msg);
            }
        }

        cleanupDrag();
    }

    function clearDragClasses() {
        livelist.querySelectorAll('.livelist-item').forEach(item => {
            item.classList.remove('drag-over', 'drag-before', 'drag-after');
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
    }
}
