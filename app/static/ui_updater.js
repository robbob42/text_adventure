// app/static/ui_updater.js
// Contains functions dedicated to updating specific UI panels in the status bar.
// Moved from script.js during Refactoring Phase 14.3
// Depends on DOM element constants defined in script.js (ensure script.js loads first)

// --- Function to Update Status Display ---
function updateStatusDisplay(statusData) {
    // Assumes hpValueElement, maxHpValueElement, etc. are defined globally by script.js
    if (!statusData) { console.warn("No status data"); return; }
    console.log("Updating status:", statusData);
    if (hpValueElement) hpValueElement.textContent = statusData.hp ?? '--';
    if (maxHpValueElement) maxHpValueElement.textContent = statusData.max_hp ?? '--';
    if (levelValueElement) levelValueElement.textContent = statusData.level ?? '--';
    if (xpValueElement) xpValueElement.textContent = statusData.xp ?? '--';
    if (xpNeededValueElement) xpNeededValueElement.textContent = statusData.xp_needed ?? '--';
}
// --- Function to Update Inventory Display ---
function updateInventoryDisplay(inventoryList) {
    // Assumes inventoryListElement is defined globally by script.js
    if (!inventoryListElement) { console.error("Inv list element missing."); return; }
    console.log("Updating inventory:", inventoryList);
    inventoryListElement.innerHTML = ''; // Clear existing list
    if (!inventoryList || inventoryList.length === 0) {
        const emptyLi = document.createElement('li'); emptyLi.textContent = '(Empty)'; inventoryListElement.appendChild(emptyLi);
    } else {
        inventoryList.forEach(item => { const li = document.createElement('li'); li.textContent = item; inventoryListElement.appendChild(li); });
    }
}
// --- Function to Update Quest Display ---
function updateQuestDisplay(questNameList) {
    // Assumes questListElement is defined globally by script.js
    if (!questListElement) { console.error("Quest list element missing."); return; }
    console.log("Updating quests:", questNameList);
    questListElement.innerHTML = ''; // Clear existing list
    if (!questNameList || questNameList.length === 0) {
        const emptyLi = document.createElement('li'); emptyLi.textContent = '(None)'; questListElement.appendChild(emptyLi);
    } else {
        questNameList.forEach(questName => { const li = document.createElement('li'); li.textContent = questName; questListElement.appendChild(li); });
    }
}

// --- Function to Update Actions Discovered Display ---
function updateActionsDisplay(discoveredList, totalCount) {
    // Assumes discoveredCountSpan, totalCountSpan, actionsListElement are defined globally
    if (!discoveredCountSpan || !totalCountSpan || !actionsListElement) {
        console.error("Actions discovered UI elements missing.");
        return;
    }
    console.log("Updating actions discovered:", discoveredList, totalCount);

    // Update counter spans
    const discoveredCount = Array.isArray(discoveredList) ? discoveredList.length : 0;
    discoveredCountSpan.textContent = discoveredCount;
    totalCountSpan.textContent = (typeof totalCount === 'number') ? totalCount : '--';

    // Update the list of actions
    actionsListElement.innerHTML = ''; // Clear existing list items

    if (discoveredCount === 0) {
        const emptyLi = document.createElement('li');
        emptyLi.textContent = '(None yet)';
        actionsListElement.appendChild(emptyLi);
    } else {
        const sortedList = [...discoveredList].sort();
        sortedList.forEach(actionVerb => {
            const li = document.createElement('li');
            li.textContent = actionVerb;
            actionsListElement.appendChild(li);
        });
    }
}

// --- Function to Update LLM Actions Discovered Display ---
function updateLlmActionsDisplay(discoveredLlmList) {
    // Assumes llmActionsGridElement is defined globally
    if (!llmActionsGridElement) {
        console.error("LLM actions grid element missing.");
        return;
    }
    console.log("Updating LLM actions discovered:", discoveredLlmList);

    // Clear the current grid content
    llmActionsGridElement.innerHTML = '';

    // Check if the list is valid and has items
    if (!Array.isArray(discoveredLlmList) || discoveredLlmList.length === 0) {
        // If empty, display the placeholder
        const placeholder = document.createElement('span');
        placeholder.classList.add('llm-action-placeholder');
        placeholder.textContent = "(Try saying 'dance' or 'sing'!)";
        llmActionsGridElement.appendChild(placeholder);
    } else {
        // If not empty, sort and create badges
        const sortedList = [...discoveredLlmList].sort();

        sortedList.forEach(actionVerb => {
            const badgeElement = document.createElement('span'); // Use span for inline-block badges
            badgeElement.classList.add('llm-action-badge'); // Add the CSS class for styling
            badgeElement.textContent = actionVerb; // Set the text to the action verb
            llmActionsGridElement.appendChild(badgeElement); // Add the badge to the grid
        });
    }
}

console.log("ui_updater.js loaded"); // Add a log to confirm loading

