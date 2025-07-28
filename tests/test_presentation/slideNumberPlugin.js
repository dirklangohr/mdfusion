// Reveal.js SlideNumberPlugin: shows slide numbers in the bottom right
let SlideNumberPlugin = {
    id: 'slideNumber',
    init: function (deck) {
        function createSlideNumbersDiv() {
            let slideNumbers = document.createElement('div');
            slideNumbers.className = 'slide-numbers';
            slideNumbers.style.position = 'absolute';
            slideNumbers.style.right = '100px';
            slideNumbers.style.bottom = '10px';
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
            let currentSlide = indices.h + indices.v + 1; // 1-based index
            let totalSlides = deck.getTotalSlides();
            let slideNumbers = createSlideNumbersDiv();
            slideNumbers.innerText = `Slide ${currentSlide} / ${totalSlides}`;
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
                let pageIndex = 0
                let totalSlides = deck.getTotalSlides();
                mutations.forEach(m => {
                    m.addedNodes.forEach(node => {
                        if (node.classList && node.classList.contains('pdf-page')) {
                            // For print, show slide number as in the main view
                            let slideNumbers = createSlideNumbersDiv();
                            slideNumbers.innerText = `Slide ${pageIndex + 1} / ${totalSlides}`;
                            node.appendChild(slideNumbers);
                            pageIndex++;
                        }
                    });
                });
            });
            obs.observe(slidesEl, { childList: true, subtree: true });
        }
    }
};