/*********************************************************************
 * THINKING PROCESS
 * 🤔🤔🤔🤠
 * 
 * Simplifying the JavaScript to:
 * 1. Remove all drag and drop functionality
 * 2. Remove animations and movements
 * 3. Focus on making the token address easily copyable
 * 4. Keep only essential functionality
 *********************************************************************/

document.addEventListener('DOMContentLoaded', () => {
    // Make token address copyable with a click
    const coinAddress = document.querySelector('.coin-address');
    if (coinAddress) {
        // Add a copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-btn';
        copyButton.innerHTML = 'Copy';
        copyButton.setAttribute('aria-label', 'Copy token address');
        
        // Insert the copy button after the address
        coinAddress.parentNode.insertBefore(copyButton, coinAddress.nextSibling);
        
        // Handle copy functionality
        copyButton.addEventListener('click', () => {
            // Create a temporary textarea to copy from
            const textarea = document.createElement('textarea');
            textarea.value = coinAddress.textContent.trim();
            document.body.appendChild(textarea);
            textarea.select();
            
            try {
                // Execute copy command
                document.execCommand('copy');
                copyButton.innerHTML = 'Copied!';
                
                // Reset button text after 2 seconds
                setTimeout(() => {
                    copyButton.innerHTML = 'Copy';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy', err);
                copyButton.innerHTML = 'Failed';
            } finally {
                document.body.removeChild(textarea);
            }
        });
    }
    
    // Add simple hover effects for links
    const links = document.querySelectorAll('a');
    links.forEach(link => {
        link.addEventListener('mouseenter', () => {
            link.style.textDecoration = 'underline';
        });
        
        link.addEventListener('mouseleave', () => {
            link.style.textDecoration = 'none';
        });
    });
});