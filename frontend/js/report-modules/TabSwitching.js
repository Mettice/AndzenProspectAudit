/**
 * TabSwitching - Handles tab switching functionality for KAV and other sections
 */

/**
 * Switch between KAV Analysis tabs (Conversion Summary, Message Type, Channel)
 * @param {string} tabName - Name of tab to switch to ('conversion', 'message-type', 'channel')
 */
function switchKAVTab(tabName) {
    console.log(`Switching to KAV tab: ${tabName}`);

    // Hide all tab content
    const allTabContents = document.querySelectorAll('.kav-tab-content');
    allTabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all tabs
    const allTabs = document.querySelectorAll('.kav-tab');
    allTabs.forEach(tab => {
        tab.classList.remove('active');
    });

    // Show target tab content
    const targetContent = document.getElementById(`kav-tab-${tabName}`);
    if (targetContent) {
        targetContent.classList.add('active');
        console.log(`✓ Activated tab content: kav-tab-${tabName}`);
    } else {
        console.warn(`Tab content not found: kav-tab-${tabName}`);
    }

    // Set active tab button (find by onclick attribute value)
    allTabs.forEach(tab => {
        const onclickAttr = tab.getAttribute('onclick');
        if (onclickAttr && onclickAttr.includes(`'${tabName}'`)) {
            tab.classList.add('active');
            console.log(`✓ Activated tab button for: ${tabName}`);
        }
    });
}

/**
 * Initialize tab switching for all tabbed sections
 */
function initializeTabSwitching() {
    console.log('Initializing tab switching...');

    // Find all tab containers
    const tabContainers = document.querySelectorAll('[data-tab-container]');

    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('[data-tab]');
        const contents = container.querySelectorAll('[data-tab-content]');

        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = tab.dataset.tab;

                // Remove active from all tabs and contents in this container
                tabs.forEach(t => t.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));

                // Add active to clicked tab and corresponding content
                tab.classList.add('active');
                const targetContent = container.querySelector(`[data-tab-content="${tabName}"]`);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    });

    console.log(`✓ Initialized ${tabContainers.length} tab containers`);
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTabSwitching);
} else {
    initializeTabSwitching();
}

// Export for global access
window.switchKAVTab = switchKAVTab;
window.initializeTabSwitching = initializeTabSwitching;
