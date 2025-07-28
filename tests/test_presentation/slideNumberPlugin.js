// Reveal.js SlideNumberPlugin: shows slide numbers in the bottom right
let SlideNumberPlugin = {
    id: 'slideNumber',
    init: function (deck) {
        let slideNumbers = document.createElement('div');
        slideNumbers.style.position = 'fixed';
        slideNumbers.style.right = '100px';
        slideNumbers.style.bottom = '10px';
        slideNumbers.style.fontSize = '20px';
        slideNumbers.style.color = '#888';
        slideNumbers.style.pointerEvents = 'none';
        slideNumbers.style.zIndex = '1001';
        document.body.appendChild(slideNumbers);

        function updateSlideNumbers() {
            let indices = deck.getIndices();
            let currentSlide = indices.h + indices.v + 1; // 1-based index
            let totalSlides = deck.getTotalSlides();
            slideNumbers.innerText = `Slide ${currentSlide} / ${totalSlides}`;
        }

        deck.on('ready', updateSlideNumbers);
        deck.on('slidechanged', updateSlideNumbers);
        deck.on('fragmentshown', updateSlideNumbers);
        deck.on('fragmenthidden', updateSlideNumbers);
        setTimeout(updateSlideNumbers, 0);
    }
};