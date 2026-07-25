document.addEventListener('DOMContentLoaded', () => {
    // --- Mouse Canvas Trail Logic ---
    const canvas = document.getElementById('trail-canvas');
    const ctx = canvas.getContext('2d');
    
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    
    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const points = [];
    // The maximum age of a point before it disappears
    const maxAge = 40; 
    
    // Only enable effect on devices with fine pointer (mouse)
    if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
        
        document.addEventListener('mousemove', (e) => {
            // Push current position to points array
            points.push({ x: e.clientX, y: e.clientY, age: 0 });
        });
        
        function animateTrail() {
            // Clear canvas for next frame
            ctx.clearRect(0, 0, width, height);
            
            // Get current theme's trail color (expecting RGB like '251, 191, 36')
            const rootStyles = getComputedStyle(document.documentElement);
            const trailColor = rootStyles.getPropertyValue('--trail-color').trim() || '251, 191, 36';

            // Draw line through points
            for (let i = 0; i < points.length - 1; i++) {
                const p1 = points[i];
                const p2 = points[i + 1];
                
                // Increase age of point
                p1.age += 1;
                
                if (p1.age > maxAge) {
                    continue;
                }
                
                // Calculate opacity: newer points are more opaque
                const opacity = Math.max(0, 1 - (p1.age / maxAge));
                
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.strokeStyle = `rgba(${trailColor}, ${opacity})`;
                
                // The line gets slightly thinner as it fades
                ctx.lineWidth = Math.max(0.5, 3 * opacity);
                ctx.lineCap = 'round';
                ctx.stroke();
            }
            
            // Age the last point too so it eventually disappears if mouse stops
            if (points.length > 0) {
                points[points.length - 1].age += 1;
            }
            
            // Remove points that are too old
            while (points.length > 0 && points[0].age > maxAge) {
                points.shift();
            }
            
            requestAnimationFrame(animateTrail);
        }
        
        // Start animation loop
        animateTrail();
    }
});
