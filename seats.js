/*********************************************************************
 * THINKING PROCESS
 * 🤔🤔🤔🤠
 * 
 * The requirements are to make "little movable boxes" for each component.
 * This means implementing drag and drop functionality for the box sections.
 * 
 * We need to:
 * 1. Make all boxes draggable (already added draggable="true" in HTML)
 * 2. Implement the drag events (dragstart, dragover, drop)
 * 3. Add visual feedback during dragging
 * 4. Support touch events for mobile
 * 5. Keep the code concise and clean
 * 
 * I'll also add some futuristic effects like a subtle hover glow
 * and element movement to enhance the UI.
 *********************************************************************/

document.addEventListener('DOMContentLoaded', () => {
    // Get all draggable elements
    const draggables = document.querySelectorAll('[draggable="true"]');
    const container = document.querySelector('.grid-container');
    
    // Track the element being dragged
    let draggedElement = null;
    
    // Add dragging events to all draggable elements
    draggables.forEach(element => {
        // Drag start - store reference and add visual effect
        element.addEventListener('dragstart', e => {
            draggedElement = element;
            element.dataset.dragging = 'true';
            e.dataTransfer.effectAllowed = 'move';
            // Create a transparent drag image
            const dragImg = document.createElement('div');
            dragImg.style.opacity = '0';
            document.body.appendChild(dragImg);
            e.dataTransfer.setDragImage(dragImg, 0, 0);
            
            // Position element absolutely during drag
            setTimeout(() => {
                element.style.position = 'absolute';
                element.style.zIndex = '1000';
            }, 0);
        });
        
        // Drag end - clean up
        element.addEventListener('dragend', () => {
            delete element.dataset.dragging;
            element.style.position = '';
            element.style.top = '';
            element.style.left = '';
            element.style.zIndex = '';
            draggedElement = null;
        });
        
        // Allow free positioning with mouse
        element.addEventListener('mousedown', e => {
            if (e.target.tagName === 'A') return; // Don't drag when clicking links
            
            const startX = e.clientX;
            const startY = e.clientY;
            const elRect = element.getBoundingClientRect();
            const offsetX = startX - elRect.left;
            const offsetY = startY - elRect.top;
            
            const moveHandler = e => {
                const x = e.clientX - offsetX;
                const y = e.clientY - offsetY;
                
                element.style.position = 'absolute';
                element.style.left = `${x}px`;
                element.style.top = `${y}px`;
                element.style.zIndex = '1000';
            };
            
            const upHandler = () => {
                document.removeEventListener('mousemove', moveHandler);
                document.removeEventListener('mouseup', upHandler);
                
                // Animate back to normal state
                setTimeout(() => {
                    element.style.transition = 'all 0.5s ease';
                    element.style.position = '';
                    element.style.left = '';
                    element.style.top = '';
                    element.style.zIndex = '';
                    setTimeout(() => {
                        element.style.transition = '';
                    }, 500);
                }, 0);
            };
            
            document.addEventListener('mousemove', moveHandler);
            document.addEventListener('mouseup', upHandler);
        });
    });
    
    // Touch events support
    draggables.forEach(element => {
        element.addEventListener('touchstart', e => {
            if (e.target.tagName === 'A') return; // Don't drag when touching links
            
            const touch = e.touches[0];
            const startX = touch.clientX;
            const startY = touch.clientY;
            const elRect = element.getBoundingClientRect();
            const offsetX = startX - elRect.left;
            const offsetY = startY - elRect.top;
            
            const moveHandler = e => {
                e.preventDefault(); // Prevent scrolling
                const touch = e.touches[0];
                const x = touch.clientX - offsetX;
                const y = touch.clientY - offsetY;
                
                element.style.position = 'absolute';
                element.style.left = `${x}px`;
                element.style.top = `${y}px`;
                element.style.zIndex = '1000';
            };
            
            const endHandler = () => {
                document.removeEventListener('touchmove', moveHandler);
                document.removeEventListener('touchend', endHandler);
                
                // Animate back to grid position
                setTimeout(() => {
                    element.style.transition = 'all 0.5s ease';
                    element.style.position = '';
                    element.style.left = '';
                    element.style.top = '';
                    element.style.zIndex = '';
                    setTimeout(() => {
                        element.style.transition = '';
                    }, 500);
                }, 0);
            };
            
            document.addEventListener('touchmove', moveHandler, { passive: false });
            document.addEventListener('touchend', endHandler);
        });
    });
    
    // Add subtle hover effect to links
    const links = document.querySelectorAll('a');
    links.forEach(link => {
        link.addEventListener('mouseenter', () => {
            link.style.textShadow = '0 0 8px var(--accent-color)';
        });
        
        link.addEventListener('mouseleave', () => {
            link.style.textShadow = '';
        });
    });
    
    // Add futuristic starfield background effect
    const createStarfield = () => {
        const stars = 100;
        const body = document.body;
        
        for (let i = 0; i < stars; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.width = `${Math.random() * 2}px`;
            star.style.height = star.style.width;
            star.style.left = `${Math.random() * 100}%`;
            star.style.top = `${Math.random() * 100}%`;
            star.style.animationDuration = `${Math.random() * 50 + 10}s`;
            star.style.opacity = Math.random() * 0.7;
            star.style.position = 'fixed';
            star.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
            star.style.borderRadius = '50%';
            star.style.zIndex = '-1';
            star.style.animation = 'twinkle ease infinite';
            
            body.appendChild(star);
        }
        
        // Add keyframes for twinkling stars
        const style = document.createElement('style');
        style.textContent = `
            @keyframes twinkle {
                0% { opacity: 0; }
                50% { opacity: 0.7; }
                100% { opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    };
    
    createStarfield();
    
    // Add pulsing animation to the token logo
    const tokenLogo = document.getElementById('thersx-logo');
    if (tokenLogo) {
        setInterval(() => {
            tokenLogo.style.transform = 'scale(1.05)';
            tokenLogo.style.boxShadow = '0 0 20px rgba(74, 135, 255, 0.9)';
            
            setTimeout(() => {
                tokenLogo.style.transform = 'scale(1)';
                tokenLogo.style.boxShadow = '0 0 15px rgba(74, 135, 255, 0.7)';
            }, 1000);
        }, 3000);
    }
});