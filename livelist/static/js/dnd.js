function initDragAndDrop(s, handle_drag_and_drop) {
    const livelist = document.querySelector("#livelist-items");
    const state = s;

    let draggedItem = null;
    let draggedItemId = null;
    let targetItem = null;

    livelist.addEventListener('dragstart', onDragStart);
    livelist.addEventListener('dragover', onDragOver);
    livelist.addEventListener('dragleave', onDragLeave);
    livelist.addEventListener('drop', onDragDrop);
    livelist.addEventListener('dragend', onDragEnd);

    function onDragStart(e) {
        if (!e.target.classList.contains('drag-handle')) {
            return;
        }

        draggedItem = e.target.closest(".livelist-item");
        draggedItemId = draggedItem.dataset.itemId;
        draggedItem.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        //e.dataTransfer.setData('text/plain', draggedItemId);

        // Hide the dragged item temporarily
        setTimeout(() => {
            //draggedItem.classList.add('d-none');
            draggedItem.classList.add('disabled');
        }, 0);
    }

    function onDragOver(e) {
        e.preventDefault();
        e.stopPropagation();

        // Check if the event target is a drag handle
        const targetItem = e.target.closest(".livelist-item");
        if (!targetItem || targetItem == draggedItem) {
            return;
        }

        targetItem.classList.add('drag-over');

        // Visual feedback: show where the item will be inserted
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

    function onDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();

        // Check if the event target is a drag handle
        const targetItem = e.target.closest(".livelist-item");
        if (!targetItem) {
            return;
        }

        targetItem.classList.remove('drag-over', 'drag-before', 'drag-after');
    }

    function onDragDrop(e) {
        e.preventDefault();
        e.stopPropagation();

        // Check if the event target is a drag handle
        const targetItem = e.target.closest(".livelist-item");
        if (!targetItem) {
            return;
        }

        // Remove drag classes
        if (draggedItem) draggedItem.classList.remove('disabled');
        if (draggedItem) draggedItem.classList.remove('dragging', 'd-none');
        if (targetItem) targetItem.classList.remove('drag-over', 'drag-before', 'drag-after');

        // Calculate new position
        if (draggedItem && targetItem && draggedItem !== targetItem) {
            const draggedPliId = draggedItem.dataset.itemId;
            const targetPliId = targetItem.dataset.itemId;

            // Determine direction
            const rect = targetItem.getBoundingClientRect();
            const before = e.clientY < rect.top + rect.height / 2;

            // Send async message to server with move instruction
            const msg = {
                moved_ids: [parseInt(draggedPliId)],
                target_id: parseInt(targetPliId),
                before: before,
                playlist_id: state.currentPlaylist,
            }

			handle_drag_and_drop(msg);
        } else {
        }

        // Reset
        draggedItem = null;
        draggedItemId = null;
    }

    function onDragEnd(e) {
        // Clean up any remaining drag classes
        const items = livelist.querySelectorAll('.list-group-item');
        items.forEach(item => {
            item.classList.remove('dragging', 'drag-over', 'drag-before', 'drag-after', 'd-none');

            item.classList.remove('disabled');
        });
    }
}
