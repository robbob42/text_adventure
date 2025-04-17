// static/script.js
// Handles frontend interaction for the LLM DM game interface.
// Updated Phase 11 Polish: Use innerHTML for game messages to render bold tags.
// Updated Phase 6, Step 6.2: Added DOM element references for Actions Discovered UI.
// Updated Phase 6, Step 6.3: Added updateActionsDisplay function.
// Updated Phase 7, Step 7.2: Call updateActionsDisplay in fetchInitialState.
// Updated Phase 7, Step 7.4: Call updateActionsDisplay in sendMessage.

// --- Get DOM Elements ---
const chatLog = document.getElementById('chat-log');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
// Status Panel Elements
const hpValueElement = document.getElementById('hp-value');
const maxHpValueElement = document.getElementById('max-hp-value');
const levelValueElement = document.getElementById('level-value');
const xpValueElement = document.getElementById('xp-value');
const xpNeededValueElement = document.getElementById('xp-needed-value');
// Inventory Panel Elements
const inventoryListElement = document.getElementById('inventory-list');
// Quests Panel Elements
const questListElement = document.getElementById('quest-list');
// Actions Discovered Panel Elements (Phase 6, Step 6.2)
const actionsCounterElement = document.getElementById('actions-counter'); // The div holding counts
const actionsListElement = document.getElementById('actions-list');     // The <ul> element
const discoveredCountSpan = actionsCounterElement ? actionsCounterElement.querySelector('span:first-child') : null; // First span in counter div
const totalCountSpan = actionsCounterElement ? actionsCounterElement.querySelector('span:last-child') : null;      // Second span in counter div


// --- Helper Function to Add Messages to Chat Log (Updated for innerHTML) ---
function addMessage(sender, text) {
    if (!chatLog) {
        console.error("Chat log element not found!");
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');

    // Basic check for potentially harmful tags - VERY basic, not foolproof!
    // A proper sanitizer library (like DOMPurify) is recommended for production apps
    // if there's ANY chance of user-controlled HTML getting into the 'text'.
    // For this game, we mostly control the backend output, but caution is advised.
    let sanitizedText = text || ""; // Ensure text is not null/undefined
    // Remove script tags entirely
    sanitizedText = sanitizedText.replace(/<script.*?>.*?<\/script>/gi, ' [removed script] ');
    // Optionally remove event handlers like onclick, onerror etc.
    // sanitizedText = sanitizedText.replace(/ on\w+=".*?"/gi, '');

    if (sender === 'Player') {
        messageDiv.classList.add('player-message');
        // Player messages should definitely use textContent for security
        messageDiv.textContent = sanitizedText; // Use textContent for player input
    } else { // Game/System messages
        // Use innerHTML for game messages to render formatting like <b>, <br>, <i>
        messageDiv.innerHTML = sanitizedText; // Use innerHTML here

        const lowerText = text ? text.toLowerCase() : "";
        // Add error class based on content
        // Check innerHTML content *after* setting it, in case tags affect text
        const renderedTextLower = messageDiv.textContent.toLowerCase();
        if (renderedTextLower.includes('[error') || lowerText.startsWith('error:') || lowerText.startsWith('sorry,') || lowerText.includes("i don't understand") || lowerText.includes("cannot") || lowerText.includes("can't ") || lowerText.includes("invalid")) {
            messageDiv.classList.add('error-message');
        } else {
            messageDiv.classList.add('game-message');
        }
    }

    chatLog.appendChild(messageDiv);

    // Auto-scroll to the bottom of the chat log
    // Use setTimeout to ensure scrolling happens after rendering
    setTimeout(() => {
        // Check if chatLog still exists (might be removed during page unload)
        if(chatLog) {
            chatLog.scrollTop = chatLog.scrollHeight;
        }
    }, 50); // Increased delay slightly
}

// --- Function to Update Status Display ---
function updateStatusDisplay(statusData) {
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
    if (!questListElement) { console.error("Quest list element missing."); return; }
    console.log("Updating quests:", questNameList);
    questListElement.innerHTML = ''; // Clear existing list
    if (!questNameList || questNameList.length === 0) {
        const emptyLi = document.createElement('li'); emptyLi.textContent = '(None)'; questListElement.appendChild(emptyLi);
    } else {
        questNameList.forEach(questName => { const li = document.createElement('li'); li.textContent = questName; questListElement.appendChild(li); });
    }
}

// --- Function to Update Actions Discovered Display (Phase 6, Step 6.3) ---
function updateActionsDisplay(discoveredList, totalCount) {
    // Check if the target elements exist
    if (!discoveredCountSpan || !totalCountSpan || !actionsListElement) {
        console.error("Actions discovered UI elements missing.");
        return;
    }
    console.log("Updating actions discovered:", discoveredList, totalCount);

    // Update counter spans
    // Use 0 as default if list is null/undefined
    const discoveredCount = Array.isArray(discoveredList) ? discoveredList.length : 0;
    discoveredCountSpan.textContent = discoveredCount;
    totalCountSpan.textContent = (typeof totalCount === 'number') ? totalCount : '--'; // Handle potential non-number total

    // Update the list of actions
    actionsListElement.innerHTML = ''; // Clear existing list items

    if (discoveredCount === 0) {
        const emptyLi = document.createElement('li');
        emptyLi.textContent = '(None yet)';
        actionsListElement.appendChild(emptyLi);
    } else {
        // Sort the list alphabetically (create a copy first)
        const sortedList = [...discoveredList].sort();

        // Create and append list items for each discovered action
        sortedList.forEach(actionVerb => {
            const li = document.createElement('li');
            li.textContent = actionVerb; // Use textContent for safety
            actionsListElement.appendChild(li);
        });
    }
}

// --- Function to Send Message to Backend ---
async function sendMessage() {
     if (!userInput || !chatLog) { console.error("DOM elements missing."); return; }
    const inputText = userInput.value.trim(); if (inputText === "") return;
    addMessage('Player', inputText); userInput.value = '';
    try {
        const response = await fetch('/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ input: inputText }), });
        // Initialize variables for data extraction
        let replyText = "[Error processing response]";
        let statusData = null;
        let inventoryData = null;
        let questData = null;
        // Add variables for actions data (Phase 7.4)
        let discoveredActionsData = null;
        let totalActionsData = null;

        if (!response.ok) {
            replyText = `Error: Server status ${response.status}.`;
            try {
                const errorData = await response.json();
                if(errorData.error) replyText = errorData.error;
                else if(errorData.reply) replyText = errorData.reply;
                // Attempt to get state even on error for UI update consistency
                statusData = errorData.character_status;
                inventoryData = errorData.inventory;
                questData = errorData.active_quests;
                discoveredActionsData = errorData.discovered_actions;
                totalActionsData = errorData.total_actions;
            } catch(e) {
                const textError = await response.text();
                console.error('Server error:', response.status, textError);
                replyText += ` Check logs.`;
            }
        } else {
            try {
                const data = await response.json();
                console.log("Received data:", data);
                if (data && data.reply !== undefined) {
                    replyText = data.reply;
                    statusData = data.character_status;
                    inventoryData = data.inventory;
                    questData = data.active_quests;
                    // Extract actions data (Phase 7.4)
                    discoveredActionsData = data.discovered_actions;
                    totalActionsData = data.total_actions;
                }
                else {
                    replyText = 'Error: Invalid response structure.';
                    console.error("Invalid response:", data);
                }
            } catch (jsonError) {
                console.error('JSON parse error:', jsonError);
                replyText = 'Error: Could not parse response.';
            }
        }
        addMessage('Game', replyText); // Add game message (using innerHTML)

        // Update UI panels
        if (statusData) updateStatusDisplay(statusData);
        if (inventoryData !== null && inventoryData !== undefined) updateInventoryDisplay(inventoryData);
        if (questData !== null && questData !== undefined) updateQuestDisplay(questData);
        // Call updateActionsDisplay with data from /chat response (Phase 7.4)
        if (discoveredActionsData !== undefined && totalActionsData !== undefined) {
            updateActionsDisplay(discoveredActionsData, totalActionsData);
        } else {
             console.warn("Actions discovered data missing or incomplete in /chat response.");
             // Optionally update with defaults if desired, but usually rely on backend sending it
             // updateActionsDisplay([], 0);
        }

    } catch (error) {
        console.error('Fetch error:', error);
        addMessage('Game', `Error: Could not connect. ${error.message}`);
    }
}
// --- Function to Fetch Initial State ---
async function fetchInitialState() {
    console.log("Fetching initial state...");
    try {
        const response = await fetch('/state');
        if (!response.ok) {
            console.error('Error fetching initial state:', response.status, await response.text());
            addMessage('System', `Error loading initial state (Status: ${response.status}).`);
            // Set default/empty states for UI
            updateStatusDisplay({ hp: '--', max_hp: '--', level: '--', xp: '--', xp_needed: '--' });
            updateInventoryDisplay([]);
            updateQuestDisplay([]);
            // Update Actions Display with defaults on error (Phase 7.2)
            updateActionsDisplay([], 0);
            return;
        }
        const data = await response.json();
        console.log("Initial state received:", data);
        // Update UI based on received data
        if (data.character_status) updateStatusDisplay(data.character_status);
        if (data.inventory !== null && data.inventory !== undefined) updateInventoryDisplay(data.inventory);
        if (data.active_quests !== null && data.active_quests !== undefined) updateQuestDisplay(data.active_quests);

        // Update Actions Discovered display (Phase 7.2)
        // Check if the expected keys exist in the response data
        if (data.discovered_actions !== undefined && data.total_actions !== undefined) {
            updateActionsDisplay(data.discovered_actions, data.total_actions);
        } else {
            // Log a warning if data is missing and use defaults
            console.warn("Actions discovered data missing or incomplete in initial state response.");
            updateActionsDisplay([], 0); // Update with default empty state
        }

    } catch (error) {
        console.error('Network error fetching initial state:', error);
        addMessage('System', `Network error loading initial state: ${error.message}.`);
        // Set default/empty states for UI on error
        updateStatusDisplay({ hp: '--', max_hp: '--', level: '--', xp: '--', xp_needed: '--' });
        updateInventoryDisplay([]);
        updateQuestDisplay([]);
        // Update Actions Display with defaults on error (Phase 7.2)
        updateActionsDisplay([], 0);
    }
}
// --- Event Listeners ---
if (sendButton) sendButton.addEventListener('click', sendMessage); else console.error("Send button missing.");
if (userInput) userInput.addEventListener('keydown', (event) => { if (event.key === 'Enter') { event.preventDefault(); sendMessage(); } }); else console.error("User input missing.");
// --- Initial Load ---
window.onload = () => { if (userInput) userInput.focus(); fetchInitialState(); };

