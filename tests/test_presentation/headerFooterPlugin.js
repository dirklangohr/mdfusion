// Reveal.js FooterPlugin: shows a centered footer and slide numbers in the bottom right
let FooterPlugin = {
    id: 'footer',
    init: function (deck) {

        function createFooter() {
            let footer = document.createElement('div');
            footer.className = 'slide-footer';
            footer.style.position = 'absolute';
            footer.style.left = '0';
            footer.style.right = '0';
            footer.style.bottom = '0px';
            footer.style.textAlign = 'center';
            footer.style.fontSize = '24px';
            footer.style.color = 'white';
            footer.style.pointerEvents = 'none';
            footer.innerText = 'My Custom Footer Text';
            return footer;
        }

        function updateFooter() {
            // Remove any existing footers to avoid duplicates
            document.querySelectorAll('.slide-footer').forEach(el => el.remove());

            footer = createFooter();
            footer.classList.add('hide-on-print');
            // add 3px to the bottom to avoid overlap with progress bar
            footer.style.bottom = '3px';
            document.querySelector('.reveal').appendChild(footer);
        }
        deck.on('ready', updateFooter);
        deck.on('slidechanged', updateFooter);
        setTimeout(updateFooter, 0);

        // Add footer for print mode
        const slidesEl = document.querySelector('.slides');
        const obs = new MutationObserver(mutations => {
            mutations.forEach(m => {
                m.addedNodes.forEach(node => {
                    if (node.classList && node.classList.contains('pdf-page')) {
                        const footer = createFooter();
                        node.appendChild(footer);
                    }
                });
            });
        });

        obs.observe(slidesEl, { childList: true, subtree: true });
    }
};
