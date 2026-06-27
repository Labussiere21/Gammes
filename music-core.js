/* ================================================================
 * music-core.js — ScalaBass / ScalaGuitare — JS partagé
 * v1.0
 *
 * Expose window.SB = { currentLang, currentNotation, prettyNote,
 *   NOTE_NAMES_EN, NOTE_NAMES_EN_SH, NOTE_NAMES_FR, NOTE_NAMES_FR_SH,
 *   getNotationTable, spellNote, initNotationLang,
 *   noteToMidi, initAudio, playSequence, playChordNotes, makePlayBtn,
 *   CHORD_INTERVALS, CHORD_LABEL, INSTRUMENTS }
 *
 * UTILISATION PAR PAGE :
 *   1. <script src="music-core.js"></script> avant le soundfont CDN
 *   2. window.SB_INSTRUMENT = 'electric_bass_finger'; // ou autre
 *      window.SB_GAIN = 3.5;
 *   3. Après migration complète d'une page : supprimer les fonctions
 *      dupliquées et utiliser SB.xxx() directement.
 *
 * Compatible pages non migrées : pas de conflit const car tout est
 * encapsulé dans un IIFE — window.SB est le seul nom global ajouté.
 * ================================================================ */

(function(global){
  'use strict';

  /* ===== NOTATION & TRADUCTIONS ===== */
  const EN_TO_FR = {
    'C':'Do','C#':'Do♯','Db':'Ré♭','D':'Ré','D#':'Ré♯','Eb':'Mi♭',
    'E':'Mi','E#':'Fa','Fb':'Mi','F':'Fa','F#':'Fa♯','Gb':'Sol♭',
    'G':'Sol','G#':'Sol♯','Ab':'La♭','A':'La','A#':'La♯','Bb':'Si♭',
    'B':'Si','B#':'Do','Cb':'Si',
    'C##':'Ré','D##':'Mi','F##':'Sol','G##':'La','A##':'Si',
    'Cbb':'Si♭','Dbb':'Do','Ebb':'Ré♭','Fbb':'Mi♭','Gbb':'Fa','Abb':'Sol♭','Bbb':'La♭',
  };

  function currentLang(){return localStorage.getItem('sblang')||'fr';}
  function currentNotation(){return localStorage.getItem('sbnot')||'en';}

  function prettyNote(noteEN){
    const clean=noteEN.replace(/♯/g,'#').replace(/♭/g,'b');
    const not=currentNotation();
    if(not==='fr'){
      if(EN_TO_FR[clean]) return EN_TO_FR[clean];
      const FR_L={C:'Do',D:'Ré',E:'Mi',F:'Fa',G:'Sol',A:'La',B:'Si'};
      const letter=clean[0]; const acc=clean.slice(1);
      return (FR_L[letter]||letter)+acc.replace(/#/g,'♯').replace(/b/g,'♭');
    }
    return clean.replace(/#/g,'♯').replace(/b/g,'♭');
  }

  /* ===== TABLES DE NOTES ===== */
  const NOTE_NAMES_EN    = ['C','D♭','D','E♭','E','F','G♭','G','A♭','A','B♭','B'];
  const NOTE_NAMES_EN_SH = ['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];
  const NOTE_NAMES_FR    = ['Do','Ré♭','Ré','Mi♭','Mi','Fa','Sol♭','Sol','La♭','La','Si♭','Si'];
  const NOTE_NAMES_FR_SH = ['Do','Do♯','Ré','Ré♯','Mi','Fa','Fa♯','Sol','Sol♯','La','La♯','Si'];

  function getNotationTable(accPref){
    const pref=(typeof state!=='undefined'&&state.accPref)||accPref||'b';
    const not=localStorage.getItem('sbnot')||'en';
    if(not==='fr') return pref==='#'?NOTE_NAMES_FR_SH:NOTE_NAMES_FR;
    return pref==='#'?NOTE_NAMES_EN_SH:NOTE_NAMES_EN;
  }
  function spellNote(pc,accPref){return getNotationTable(accPref)[pc];}

  function initNotationLang(){
    const ns=document.getElementById('notation-seg');
    if(ns){
      const stored=localStorage.getItem('sbnot')||'en';
      ns.querySelectorAll('button').forEach(b=>{
        b.classList.toggle('on', b.dataset.notation===stored);
      });
      ns.addEventListener('click', e=>{
        const b=e.target.closest('button[data-notation]'); if(!b) return;
        localStorage.setItem('sbnot', b.dataset.notation);
        ns.querySelectorAll('button').forEach(x=>x.classList.toggle('on', x===b));
        if(typeof render==='function') render();
        else { if(typeof buildPiano==='function') buildPiano(); if(typeof updateI18n==='function') updateI18n(); }
      });
    }
    const ls=document.getElementById('lang-seg');
    if(ls){
      const stored=localStorage.getItem('sblang')||'fr';
      ls.querySelectorAll('button').forEach(b=>{
        b.classList.toggle('on', b.dataset.lang===stored);
      });
      ls.addEventListener('click', e=>{
        const b=e.target.closest('button[data-lang]'); if(!b) return;
        localStorage.setItem('sblang', b.dataset.lang);
        ls.querySelectorAll('button').forEach(x=>x.classList.toggle('on', x===b));
        if(typeof render==='function') render();
        else { if(typeof buildPiano==='function') buildPiano(); if(typeof updateI18n==='function') updateI18n(); }
      });
    }
  }

  /* ===== MODULE AUDIO (paramétrable par page) ===== */
  let _sfInst=null,_audioCtx=null,_audioLoading=false;

  const NOTE_MAP_AUDIO={
    'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'E#':5,
    'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,
    'Bb':10,'B':11,'B#':0,'Cb':11,
    'Do':0,'Ré':2,'Mi':4,'Fa':5,'Sol':7,'La':9,'Si':11,
  };

  function noteToMidi(n,oct){
    const clean=n.replace('♯','#').replace('♭','b').replace('𝄫','bb');
    const pc=NOTE_MAP_AUDIO[clean]??0;
    return (oct+1)*12+pc;
  }

  /* Chaque page définit window.SB_INSTRUMENT et window.SB_GAIN avant
   * d'appeler initAudio(). Défauts : basse électrique, gain 3.5. */
  async function initAudio(){
    if(_sfInst) return _sfInst;
    if(_audioLoading) return null;
    _audioLoading=true;
    const instrument=global.SB_INSTRUMENT||'electric_bass_finger';
    const gain=global.SB_GAIN||3.5;
    try{
      _audioCtx=new(global.AudioContext||global.webkitAudioContext)();
      _sfInst=await Soundfont.instrument(_audioCtx,instrument,{
        soundfont:'MusyngKite',
        nameToUrl:(name,sf,fmt)=>`https://gleitz.github.io/midi-js-soundfonts/${sf}/${name}-${fmt}.js`,
        format:'mp3',gain,
      });
      return _sfInst;
    }catch(e){console.warn('Audio:',e);_audioLoading=false;return null;}
  }

  async function playSequence(notes,bpm=80,oct=2){
    const inst=await initAudio(); if(!inst)return;
    if(_audioCtx.state==='suspended') await _audioCtx.resume();
    const beat=60/bpm;
    notes.forEach((n,i)=>{
      const midi=typeof n==='number'?n:noteToMidi(n,oct);
      inst.play(midi,_audioCtx.currentTime+i*beat,{duration:beat*0.9,gain:3});
    });
  }

  async function playChordNotes(notes,oct=2){
    const inst=await initAudio(); if(!inst)return;
    if(_audioCtx.state==='suspended') await _audioCtx.resume();
    notes.forEach((n,i)=>{
      const midi=typeof n==='number'?n:noteToMidi(n,oct);
      inst.play(midi,_audioCtx.currentTime+i*0.05,{duration:1.5,gain:3});
    });
  }

  function makePlayBtn(onClick,title='Écouter',lbl='▶'){
    const b=document.createElement('button');
    b.className='play-btn'; b.innerHTML=lbl; b.title=title;
    let playing=false;
    b.onclick=async(e)=>{
      e.stopPropagation();
      if(playing)return;
      playing=true; b.innerHTML='■'; b.classList.add('playing');
      try{await onClick();}catch(err){console.warn(err);}
      setTimeout(()=>{playing=false;b.innerHTML=lbl;b.classList.remove('playing');},4000);
    };
    return b;
  }

  /* ===== INTERVALLES & ACCORDS ===== */
  const CHORD_INTERVALS={
    '':    [0,4,7],
    'm':   [0,3,7],
    '7':   [0,4,7,10],
    'm7':  [0,3,7,10],
    'maj7':[0,4,7,11],
    'm7b5':[0,3,6,10],
    'dim': [0,3,6],
    'dim7':[0,3,6,9],
    '5':   [0,7],
    '7b9': [0,4,7,10,1],
    /* suspendus */
    'sus4':[0,5,7],
    'sus2':[0,2,7],
    /* augmenté */
    'aug': [0,4,8],
    /* neuvièmes */
    'maj9':[0,4,7,11,2],
    'm9':  [0,3,7,10,2],
    '9':   [0,4,7,10,2],
  };

  const CHORD_LABEL={
    '':'','m':'m','7':'7','m7':'m7','maj7':'maj7',
    'm7b5':'m7♭5','dim':'°','dim7':'°7','5':'5','7b9':'7♭9',
    'sus4':'sus4','sus2':'sus2','aug':'+',
    'maj9':'maj9','m9':'m9','9':'9',
  };

  /* ===== INSTRUMENTS & ACCORDAGES (Mission 3) ===== */
  const INSTRUMENTS={
    bass:{
      soundfont:'electric_bass_finger',
      gain:3.5,
      tunings:{
        4:{
          standard:{label:'Standard',    notes:['E','A','D','G'],     midi:[28,33,38,43]},
          drop_d:  {label:'Drop D',      notes:['D','A','D','G'],     midi:[26,33,38,43]},
        },
        5:{
          standard:{label:'Standard 5',  notes:['B','E','A','D','G'], midi:[23,28,33,38,43]},
        },
        6:{
          standard:{label:'Standard 6',  notes:['B','E','A','D','G','C'],midi:[23,28,33,38,43,48]},
        },
      },
    },
    guitar:{
      soundfont:'acoustic_guitar_steel',
      gain:2.5,
      tunings:{
        6:{
          standard:{label:'Standard',    notes:['E','A','D','G','B','E'], midi:[40,45,50,55,59,64]},
          drop_d:  {label:'Drop D',      notes:['D','A','D','G','B','E'], midi:[38,45,50,55,59,64]},
          open_g:  {label:'Open G',      notes:['D','G','D','G','B','D'], midi:[38,43,50,55,59,62]},
        },
        7:{
          standard:{label:'Standard 7',  notes:['B','E','A','D','G','B','E'],midi:[35,40,45,50,55,59,64]},
        },
      },
    },
  };

  /* ===== EXPORT ===== */
  global.SB={
    currentLang,
    currentNotation,
    prettyNote,
    NOTE_NAMES_EN,
    NOTE_NAMES_EN_SH,
    NOTE_NAMES_FR,
    NOTE_NAMES_FR_SH,
    getNotationTable,
    spellNote,
    initNotationLang,
    noteToMidi,
    initAudio,
    playSequence,
    playChordNotes,
    makePlayBtn,
    CHORD_INTERVALS,
    CHORD_LABEL,
    INSTRUMENTS,
  };

})(window);
