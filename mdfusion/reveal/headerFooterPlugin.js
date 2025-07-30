// Reveal.js FooterPlugin: shows a centered footer and slide numbers in the bottom right
let FooterPlugin = {
    id: 'footer',
    init: function (deck) {

        const hideFooterOnPages = [0]

        function createFooter({ bottom = 10, bottomExtra = 0 } = {}) {
            let footer = document.createElement('div');
            footer.className = 'slide-footer';
            footer.style.position = 'absolute';
            footer.style.left = '0';
            footer.style.right = '0';
            footer.style.bottom = `${bottom + bottomExtra}px`;
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

            let indices = deck.getIndices();
            let currentSlide = indices.h + indices.v; // 1-based index
            if (hideFooterOnPages.includes(currentSlide)) {
                return;
            }

            footer = createFooter({ bottomExtra: 3 });
            footer.classList.add('hide-on-print');
            document.querySelector('.reveal').appendChild(footer);
        }
        deck.on('ready', updateFooter);
        deck.on('slidechanged', updateFooter);
        setTimeout(updateFooter, 0);

        // Add footer for print mode
        const slidesEl = document.querySelector('.slides');
        const obs = new MutationObserver(mutations => {
            mutations.forEach((m, i) => {
                m.addedNodes.forEach(node => {
                    if (hideFooterOnPages.includes(i)) {
                        return
                    }
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
