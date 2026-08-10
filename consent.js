/* ============================================================
   Bandeau de consentement — Google Consent Mode v2
   ------------------------------------------------------------
   Les defauts sont poses a 'denied' dans le <head> de chaque page,
   AVANT le chargement de gtag.js : aucun cookie de mesure n'est
   depose tant que le visiteur n'a pas clique.
   Refuser est aussi simple qu'accepter (un clic, meme poids visuel) :
   c'est une exigence CNIL, pas un choix esthetique. Le lien
   « Gestion des cookies » mene a cookies.html, ou le choix reste
   modifiable a tout moment.
   ============================================================ */
(function () {
  var KEY = 'sbconsent';

  var TXT = {
    fr: {
      msg: 'Ce site utilise Google Analytics pour mesurer son audience. Aucune donnée n’est envoyée avant votre accord.',
      no: 'Refuser', yes: 'Accepter', manage: 'Gestion des cookies'
    },
    en: {
      msg: 'This site uses Google Analytics to measure its audience. No data is sent before you agree.',
      no: 'Decline', yes: 'Accept', manage: 'Cookie settings'
    }
  };

  function lang() { try { return localStorage.getItem('sblang') === 'en' ? 'en' : 'fr'; } catch (e) { return 'fr'; } }
  function store(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }

  function apply(granted) {
    if (typeof gtag !== 'function') return;
    gtag('consent', 'update', { analytics_storage: granted ? 'granted' : 'denied' });
  }
  window.sbConsentApply = apply;
  window.sbConsentGet = stored;
  window.sbConsentSet = function (v) { store(v); apply(v === 'granted'); };

  function build() {
    var t = TXT[lang()];
    var bar = document.createElement('div');
    bar.id = 'sb-consent';
    bar.setAttribute('role', 'dialog');
    bar.style.cssText = [
      'position:fixed', 'left:0', 'right:0', 'bottom:0', 'z-index:99999',
      'display:flex', 'flex-wrap:wrap', 'gap:14px', 'align-items:center',
      'justify-content:center', 'padding:14px clamp(12px,4vw,28px)',
      'background:#160f08', 'border-top:1px solid #3a2a18',
      'font-family:"Hanken Grotesk",system-ui,sans-serif', 'font-size:13px',
      'color:#d8cbbb', 'line-height:1.5', 'box-shadow:0 -6px 24px rgba(0,0,0,.45)'
    ].join(';');

    var p = document.createElement('span');
    p.textContent = t.msg;
    p.style.cssText = 'max-width:58ch';

    var wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;gap:10px;align-items:center;flex-shrink:0;flex-wrap:wrap';

    function mk(label, primary) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      // Refuser et Accepter ont exactement la meme taille et le meme
      // contraste : aucun des deux n'est mis en avant.
      b.style.cssText = [
        'font-family:inherit', 'font-size:13px', 'font-weight:600',
        'padding:9px 20px', 'border-radius:8px', 'cursor:pointer',
        'min-width:112px', 'border:1px solid #d9a849',
        'background:' + (primary ? '#d9a849' : 'transparent'),
        'color:' + (primary ? '#160f08' : '#e8dccb')
      ].join(';');
      return b;
    }

    var no = mk(t.no, false), yes = mk(t.yes, true);
    no.onclick = function () { store('denied'); apply(false); bar.remove(); };
    yes.onclick = function () { store('granted'); apply(true); bar.remove(); };

    var manage = document.createElement('a');
    manage.href = '/cookies.html';
    manage.textContent = t.manage;
    manage.style.cssText = 'color:#b9a894;font-size:12px;text-decoration:underline;white-space:nowrap';

    wrap.appendChild(no); wrap.appendChild(yes); wrap.appendChild(manage);
    bar.appendChild(p); bar.appendChild(wrap);
    document.body.appendChild(bar);
  }

  window.sbConsentReset = function () {
    try { localStorage.removeItem(KEY); } catch (e) {}
    apply(false);
    if (!document.getElementById('sb-consent')) build();
  };

  if (stored()) return;               // choix deja exprime
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
