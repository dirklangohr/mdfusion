// Reveal.js SlideNumberPlugin: shows slide numbers in the bottom right
let SlideNumberPlugin = {
    id: 'slideNumber',
    init: function (deck) {
        const hideSlideNumbersOnPages = [0];

        function createSlideNumbersDiv({ bottom = 10, bottomExtra = 0, offsetRight = 100 } = {}) {
            let slideNumbers = document.createElement('div');
            slideNumbers.className = 'slide-numbers';
            slideNumbers.style.position = 'absolute';
            slideNumbers.style.right = `${offsetRight}px`;
            slideNumbers.style.bottom = `${bottom + bottomExtra}px`;
            slideNumbers.style.fontSize = '24px';
            slideNumbers.style.color = 'white';
            slideNumbers.style.pointerEvents = 'none';
            slideNumbers.style.zIndex = '1001';
            return slideNumbers;
        }

        function updateSlideNumbers() {
            // Remove any existing slide numbers to avoid duplicates
            document.querySelectorAll('.slide-numbers').forEach(el => el.remove());
            let indices = deck.getIndices();
            let currentSlide = indices.h + indices.v;
            let totalSlides = deck.getTotalSlides();
            if (hideSlideNumbersOnPages.includes(currentSlide)) {
                return;
            }

            let slideNumbers = createSlideNumbersDiv({ bottomExtra: 3 });
            slideNumbers.innerText = `${currentSlide + 1} / ${totalSlides}`;
            let reveal = document.querySelector('.reveal');
            if (reveal) {
                reveal.appendChild(slideNumbers);
            }
        }

        deck.on('ready', updateSlideNumbers);
        deck.on('slidechanged', updateSlideNumbers);
        deck.on('fragmentshown', updateSlideNumbers);
        deck.on('fragmenthidden', updateSlideNumbers);
        setTimeout(updateSlideNumbers, 0);

        // Add slide numbers for print mode (PDF export)
        const slidesEl = document.querySelector('.slides');
        if (slidesEl) {
            const obs = new MutationObserver(mutations => {
                let pageIndex = -1 // start at -1
                let totalSlides = deck.getTotalSlides();
                mutations.forEach(m => {
                    m.addedNodes.forEach(node => {
                        if (node.classList && node.classList.contains('pdf-page')) {
                            pageIndex++;
                            if (hideSlideNumbersOnPages.includes(pageIndex)) {
                                return;
                            }
                            // For print, show slide number as in the main view
                            let slideNumbers = createSlideNumbersDiv({ offsetRight: 10 });
                            slideNumbers.innerText = `${pageIndex + 1} / ${totalSlides}`;
                            node.appendChild(slideNumbers);
                        }
                    });
                });
            });
            obs.observe(slidesEl, { childList: true, subtree: true });
        }
    }
};