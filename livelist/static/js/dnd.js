function initDragAndDrop(s, handle_drag_and_drop) {
    const livelist = document.querySelector("#livelist-items");
    const state = s;

    let draggedItem = null;
    let draggedItemId = null;
    let isDragging = false;
    let startClientY = 0;
    let startClientX = 0;

    // Minimum distance in px before a pointer-down is considered a drag
    const DRAG_THRESHOLD = 5;

    livelist.addEventListener('pointerdown', onPointerDown);

    function onPointerDown(e) {
        const handle = e.target.closest('.drag-handle');
        if (!handle) return;

        const item = handle.closest('.livelist-item');
        if (!item) return;

        draggedItem = item;
        draggedItemId = item.dataset.itemId;
        isDragging = false;
        startClientX = e.clientX;
        startClientY = e.clientY;

        // Listen on document so we receive move/up regardless of where the
        // pointer travels.  We do NOT call setPointerCapture here – doing so
        // would prevent the browser from dispatching the normal click event
        // that the rest of the application relies on.
        document.addEventListener('pointermove', onPointerMove);
        document.addEventListener('pointerup', onPointerUp);
        document.addEventListener('pointercancel', onPointerUp);
    }

    function onPointerMove(e) {
        if (!draggedItem) return;

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

            // Now that we are definitely dragging, capture the pointer for
            // reliable event tracking and to suppress the click that would
            // otherwise fire on pointerup.
            livelist.setPointerCapture(e.pointerId);
        }

        // Hide the dragged item's real element temporarily so that
        // elementFromPoint returns the element *underneath* it.
        draggedItem.style.display = 'none';

        const targetEl = document.elementFromPoint(e.clientX, e.clientY);

        // Restore visibility immediately.
        draggedItem.style.display = '';

        // Clear visual feedback from all items.
        clearDragClasses();

        if (!targetEl) return;

        const targetItem = targetEl.closest('.livelist-item');
        if (!targetItem || targetItem === draggedItem) return;

        targetItem.classList.add('drag-over');

        const rect = targetItem.getBoundingClientRect();
        const before = e.clientY < rect.top + rect.height / 2;

        if (before) {
            targetItem.classList.add('drag-before');
            targetItem.classList.remove('drag-after');
        } else {
            targetItem.classList.add('drag-after');
            targetItem.classList.remove('drag-before');
        }
    }

    function onPointerUp(e) {
        document.removeEventListener('pointermove', onPointerMove);
        document.removeEventListener('pointerup', onPointerUp);
        document.removeEventListener('pointercancel', onPointerUp);

        if (isDragging) {
            try {
                livelist.releasePointerCapture(e.pointerId);
            } catch (_) {
                // May already be released
            }
        }

        if (!draggedItem) return;

        if (isDragging) {
            // Determine the drop target from the final pointer position.
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

        // Clean up
        cleanupDrag();
    }

    function clearDragClasses() {
        livelist.querySelectorAll('.livelist-item').forEach(item => {
            item.classList.remove('drag-over', 'drag-before', 'drag-after');
        });
    }

    function cleanupDrag() {
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
