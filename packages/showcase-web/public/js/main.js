/**
 * La Boîte à Geeks Studios — LBG (Showcase Interactive Scripts)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Console welcome message pour les explorateurs du code
  console.log(
    '%c⚡ La Boîte à Geeks Studios — LBG ⚡\n%cMondes persistants, agents autonomes & IA incarnée.\nArchitecture 100% souveraine.',
    'color: #00f5d4; font-size: 16px; font-weight: bold; background: #070a13; padding: 4px 8px; border-radius: 4px;',
    'color: #a855f7; font-size: 12px; margin-top: 4px;'
  );

  // Effet interactif de glow suivant la souris sur les cartes
  const cards = document.querySelectorAll('.card, .stat-card');
  cards.forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });

  // Défilement fluide vers les ancres
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId && targetId !== '#') {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });
});
