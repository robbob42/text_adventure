// static/script.js
// Handles frontend interaction for the LLM DM game interface.
// Refactored: Moved UI update functions to ui_updater.js (Phase 14.3)

// --- Get DOM Elements ---
// These need to be defined before ui_updater.js is loaded if it relies on them globally
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
// Actions Discovered Panel Elements
const actionsCounterElement = document.getElementById('actions-counter');
const actionsListElement = document.getElementById('actions-list');
const discoveredCountSpan = actionsCounterElement ? actionsCounterElement.querySelector('span:first-child') : null;
const totalCountSpan = actionsCounterElement ? actionsCounterElement.querySelector('span:last-child') : null;
// LLM Actions Discovered Panel Elements
const llmActionsGridElement = document.getElementById('llm-actions-grid');


// --- Helper Function to Add Messages to Chat Log ---
// (Remains the same as before)
function addMessage(sender, text) {
    if (!chatLog) {
        console.error("Chat log element not found!");
        return;
    }
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    let sanitizedText = text || "";
    sanitizedText = sanitizedText.replace(/<script.*?>.*?<\/script>/gi, ' [removed script] ');

    if (sender === 'Player') {
        messageDiv.classList.add('player-message');
        messageDiv.textContent = sanitizedText;
    } else {
        messageDiv.innerHTML = sanitizedText;
        const lowerText = text ? text.toLowerCase() : "";
        const renderedTextLower = messageDiv.textContent.toLowerCase();
        if (renderedTextLower.includes('[error') || lowerText.startsWith('error:') || lowerText.startsWith('sorry,') || lowerText.includes("i don't understand") || lowerText.includes("cannot") || lowerText.includes("can't ") || lowerText.includes("invalid")) {
            messageDiv.classList.add('error-message');
        } else {
            messageDiv.classList.add('game-message');
        }
    }
    chatLog.appendChild(messageDiv);
    setTimeout(() => {
        if(chatLog) {
            chatLog.scrollTop = chatLog.scrollHeight;
        }
    }, 50);
}

// --- UI Update Functions Removed (Moved to ui_updater.js) ---
// function updateStatusDisplay(statusData) { ... }
// function updateInventoryDisplay(inventoryList) { ... }
// function updateQuestDisplay(questNameList) { ... }
// function updateActionsDisplay(discoveredList, totalCount) { ... }
// function updateLlmActionsDisplay(discoveredLlmList) { ... }


// --- Function to Send Message to Backend ---
// Calls the update functions now defined in ui_updater.js
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
        let discoveredActionsData = null;
        let totalActionsData = null;
        let discoveredLlmActionsData = null;

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
                discoveredLlmActionsData = errorData.discovered_llm_actions;
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
                    discoveredActionsData = data.discovered_actions;
                    totalActionsData = data.total_actions;
                    discoveredLlmActionsData = data.discovered_llm_actions;
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

        // Update UI panels by calling functions now defined in ui_updater.js
        if (statusData) updateStatusDisplay(statusData);
        if (inventoryData !== null && inventoryData !== undefined) updateInventoryDisplay(inventoryData);
        if (questData !== null && questData !== undefined) updateQuestDisplay(questData);
        if (discoveredActionsData !== undefined && totalActionsData !== undefined) {
            updateActionsDisplay(discoveredActionsData, totalActionsData);
        } else {
             console.warn("Actions discovered data missing or incomplete in /chat response.");
        }
        if (discoveredLlmActionsData !== undefined) {
            updateLlmActionsDisplay(discoveredLlmActionsData);
        } else {
             console.warn("LLM actions discovered data missing or incomplete in /chat response.");
        }

    } catch (error) {
        console.error('Fetch error:', error);
        addMessage('Game', `Error: Could not connect. ${error.message}`);
    }
}
// --- Function to Fetch Initial State ---
// Calls the update functions now defined in ui_updater.js
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
            updateActionsDisplay([], 0);
            updateLlmActionsDisplay([]); // Call LLM updater with default
            return;
        }
        const data = await response.json();
        console.log("Initial state received:", data);
        // Update UI based on received data
        if (data.character_status) updateStatusDisplay(data.character_status);
        if (data.inventory !== null && data.inventory !== undefined) updateInventoryDisplay(data.inventory);
        if (data.active_quests !== null && data.active_quests !== undefined) updateQuestDisplay(data.active_quests);
        if (data.discovered_actions !== undefined && data.total_actions !== undefined) {
            updateActionsDisplay(data.discovered_actions, data.total_actions);
        } else {
            console.warn("Actions discovered data missing or incomplete in initial state response.");
            updateActionsDisplay([], 0);
        }
        if (data.discovered_llm_actions !== undefined) {
            updateLlmActionsDisplay(data.discovered_llm_actions);
        } else {
            console.warn("LLM actions discovered data missing in initial state response.");
            updateLlmActionsDisplay([]);
        }

    } catch (error) {
        console.error('Network error fetching initial state:', error);
        addMessage('System', `Network error loading initial state: ${error.message}.`);
        // Set default/empty states for UI on error
        updateStatusDisplay({ hp: '--', max_hp: '--', level: '--', xp: '--', xp_needed: '--' });
        updateInventoryDisplay([]);
        updateQuestDisplay([]);
        updateActionsDisplay([], 0);
        updateLlmActionsDisplay([]); // Call LLM updater with default
    }
}
// --- Event Listeners ---
if (sendButton) sendButton.addEventListener('click', sendMessage); else console.error("Send button missing.");
if (userInput) userInput.addEventListener('keydown', (event) => { if (event.key === 'Enter') { event.preventDefault(); sendMessage(); } }); else console.error("User input missing.");
// --- Initial Load ---
window.onload = () => { if (userInput) userInput.focus(); fetchInitialState(); };

console.log("script.js loaded"); // Add a log to confirm loading

