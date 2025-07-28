// Reveal.js FooterPlugin: shows a centered footer and slide numbers in the bottom right
let FooterPlugin = {
    id: 'footer',
    init: function (deck) {
        // Centered footer only
        let footer = document.createElement('div');
        footer.style.position = 'fixed';
        footer.style.left = '0';
        footer.style.right = '0';
        footer.style.bottom = '10px';
        footer.style.textAlign = 'center';
        footer.style.fontSize = '36px';
        footer.style.color = '#888';
        footer.style.pointerEvents = 'none';
        footer.style.zIndex = '1000';
        document.body.appendChild(footer);

        function updateFooter() {
            footer.innerText = `My Custom Footer Text`;
        }

        deck.on('ready', updateFooter);
        deck.on('slidechanged', updateFooter);
        setTimeout(updateFooter, 0);
    }
};
