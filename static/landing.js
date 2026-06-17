/* ── Landing Page JS ──────────────────────── */

// Generate floating particles
(function createParticles() {
  const container = document.getElementById('hero-particles');
  if (!container) return;
  for (let i = 0; i < 60; i++) {
    const p = document.createElement('div');
    const size = Math.random() * 3 + 1;
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    const delay = Math.random() * 6;
    const dur = 4 + Math.random() * 6;
    const isGold = Math.random() > 0.7;
    p.style.cssText = `
      position:absolute;
      left:${x}%;top:${y}%;
      width:${size}px;height:${size}px;
      border-radius:50%;
      background:${isGold ? 'rgba(255,215,0,0.8)' : 'rgba(232,93,244,0.6)'};
      box-shadow:0 0 ${size*3}px ${isGold ? 'rgba(255,215,0,0.6)' : 'rgba(232,93,244,0.4)'};
      animation:particleFloat ${dur}s ${delay}s ease-in-out infinite alternate;
      pointer-events:none;
    `;
    container.appendChild(p);
  }

  // Inject keyframes
  const style = document.createElement('style');
  style.textContent = `
    @keyframes particleFloat {
      0%   { transform: translateY(0px) scale(1);   opacity: 0.4; }
      50%  { transform: translateY(-20px) scale(1.2); opacity: 1; }
      100% { transform: translateY(5px) scale(0.9);  opacity: 0.2; }
    }
  `;
  document.head.appendChild(style);
})();

// Nav scroll effect
window.addEventListener('scroll', () => {
  const nav = document.getElementById('top-nav');
  if (!nav) return;
  if (window.scrollY > 20) {
    nav.style.background = 'rgba(10,2,22,0.97)';
    nav.style.boxShadow = '0 4px 20px rgba(0,0,0,0.4)';
  } else {
    nav.style.background = 'rgba(15,4,30,0.88)';
    nav.style.boxShadow = 'none';
  }
});

// Register button ripple
const regBtn = document.getElementById('register-now-btn');
if (regBtn) {
  regBtn.addEventListener('mouseenter', () => {
    regBtn.style.letterSpacing = '3px';
  });
  regBtn.addEventListener('mouseleave', () => {
    regBtn.style.letterSpacing = '2px';
  });
}

// Welcome Popup
document.addEventListener('DOMContentLoaded', () => {
  const popup = document.getElementById('welcome-popup');
  const closeBtn = document.getElementById('close-popup');
  const popupLink = document.getElementById('popup-link');

  if (popup && closeBtn) {
    // Show popup with a slight delay
    setTimeout(() => {
      popup.classList.add('active');
    }, 500);

    // Close on button click
    closeBtn.addEventListener('click', () => {
      popup.classList.remove('active');
    });

    // Close on clicking the image link
    if (popupLink) {
      popupLink.addEventListener('click', () => {
        popup.classList.remove('active');
      });
    }

    // Close on clicking outside the image
    popup.addEventListener('click', (e) => {
      if (e.target === popup) {
        popup.classList.remove('active');
      }
    });
  }
});
