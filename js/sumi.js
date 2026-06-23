/* =========================================================
   ヒロラボ — Sumi Hero JS
   雅楽風アンビエントBGM（Web Audio API で合成）
   + 筆アニメーション（requestAnimationFrame + SVG getPointAtLength）
   ========================================================= */

(function () {
  'use strict';

  // ===== BGM =====
  const btn = document.getElementById('sumi-bgm');
  if (btn) {
    const params = new URLSearchParams(location.search);
    if (params.get('mute') === '1') {
      btn.style.display = 'none';
    }

    let ctx = null;
    let masterGain = null;
    let playing = false;
    let oscillators = [];
    let noteTimer = null;
    const scale = [220.00, 261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25, 783.99];

    function createReverb(ctx, duration = 4, decay = 2) {
      const sampleRate = ctx.sampleRate;
      const length = sampleRate * duration;
      const impulse = ctx.createBuffer(2, length, sampleRate);
      for (let ch = 0; ch < 2; ch++) {
        const data = impulse.getChannelData(ch);
        for (let i = 0; i < length; i++) {
          data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, decay);
        }
      }
      const convolver = ctx.createConvolver();
      convolver.buffer = impulse;
      return convolver;
    }

    function start() {
      if (playing) return;
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      masterGain = ctx.createGain();
      masterGain.gain.value = 0;
      masterGain.gain.linearRampToValueAtTime(0.06, ctx.currentTime + 3);

      const reverb = createReverb(ctx, 5, 2.5);
      const reverbGain = ctx.createGain();
      reverbGain.gain.value = 0.45;
      reverb.connect(reverbGain);
      reverbGain.connect(masterGain);
      masterGain.connect(ctx.destination);

      const drones = [110.00, 165.00, 220.00];
      drones.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        osc.type = i === 0 ? 'sine' : 'triangle';
        osc.frequency.value = freq;
        const g = ctx.createGain();
        g.gain.value = 0.5 / (i + 1.5);
        osc.connect(g);
        g.connect(masterGain);
        g.connect(reverb);
        osc.start();
        oscillators.push({ osc, gain: g, baseGain: g.gain.value });
      });

      function scheduleNote() {
        if (!playing || !ctx) return;
        const now = ctx.currentTime;
        const freq = scale[Math.floor(Math.random() * scale.length)];
        const osc = ctx.createOscillator();
        osc.type = ['sine', 'triangle', 'sine'][Math.floor(Math.random() * 3)];
        osc.frequency.value = freq;
        const noteGain = ctx.createGain();
        const vol = 0.04 + Math.random() * 0.03;
        noteGain.gain.setValueAtTime(0, now);
        noteGain.gain.linearRampToValueAtTime(vol, now + 0.05);
        noteGain.gain.exponentialRampToValueAtTime(0.0001, now + 4 + Math.random() * 3);
        osc.connect(noteGain);
        noteGain.connect(reverb);
        noteGain.connect(masterGain);
        osc.start(now);
        osc.stop(now + 8);
        const next = 3000 + Math.random() * 6000;
        noteTimer = setTimeout(scheduleNote, next);
      }

      scheduleNote();
      playing = true;
      btn.dataset.playing = 'true';
      btn.textContent = '♪ 音 ON';
    }

    function stop() {
      if (!playing || !ctx) return;
      playing = false;
      btn.dataset.playing = 'false';
      btn.textContent = '♪ 音 OFF';
      if (noteTimer) {
        clearTimeout(noteTimer);
        noteTimer = null;
      }
      masterGain.gain.cancelScheduledValues(ctx.currentTime);
      masterGain.gain.linearRampToValueAtTime(0, ctx.currentTime + 1.5);
      setTimeout(() => {
        oscillators.forEach(({ osc }) => { try { osc.stop(); } catch (e) {} });
        oscillators = [];
        ctx.close().catch(() => {});
        ctx = null;
      }, 1700);
    }

    btn.addEventListener('click', () => {
      if (playing) stop();
      else start();
    });

    window.addEventListener('beforeunload', () => {
      if (playing && ctx) {
        if (noteTimer) clearTimeout(noteTimer);
        oscillators.forEach(({ osc }) => { try { osc.stop(); } catch (e) {} });
        ctx.close().catch(() => {});
      }
    });
  }

  // ===== 筆アニメーション（JS制御） =====
  const hero = document.querySelector('.sumi-hero');
  if (!hero) return;

  // 各筆の設定：brush要素, stroke要素, 正規化path, 開始遅延(ms), 持続時間(ms)
  const brushes = [
    { brush: document.querySelector('.brush-1'), stroke: document.querySelector('.ink-stroke.s1'), path: 'M 0.08,0.42 C 0.20,0.25 0.32,0.28 0.43,0.42 S 0.62,0.67 0.78,0.58 0.94,0.39 1.00,0.28', delay: 800,  duration: 14000 },
    { brush: document.querySelector('.brush-2'), stroke: document.querySelector('.ink-stroke.s2'), path: 'M 0.12,0.80 C 0.25,0.70 0.36,0.86 0.50,0.80 S 0.74,0.70 0.86,0.84 0.96,0.92 1.00,0.88', delay: 3200,  duration: 12000 },
    { brush: document.querySelector('.brush-3'), stroke: document.querySelector('.ink-stroke.s3'), path: 'M 0.16,0.25 Q 0.30,0.14 0.42,0.25 T 0.69,0.33 Q 0.80,0.42 0.92,0.31', delay: 5600,  duration: 10000 },
    { brush: document.querySelector('.brush-4'), stroke: document.querySelector('.ink-stroke.s4'), path: 'M 0.08,0.95 C 0.22,0.88 0.34,0.98 0.47,0.92 S 0.69,0.85 0.81,0.93', delay: 7800,  duration: 9000 },
    { brush: document.querySelector('.brush-5'), stroke: document.querySelector('.ink-stroke.s5'), path: 'M 0.27,0.64 Q 0.41,0.55 0.53,0.66 T 0.78,0.72', delay: 9800, duration: 7000 }
  ];

  // 画面座標に合わせてpathを transform: 0-1 -> px に置換
  function resolvePaths() {
    const rect = hero.getBoundingClientRect();
    const W = rect.width;
    const H = rect.height;
    brushes.forEach(b => {
      if (b.path && !b._resolved) {
        b._resolvedPath = b.path.replace(/([MLCQTS])?\s*([-\d.]+),([-\d.]+)/g, (m, cmd, x, y) => {
          const X = (parseFloat(x) * W).toFixed(1);
          const Y = (parseFloat(y) * H).toFixed(1);
          return (cmd ? cmd + ' ' : '') + X + ',' + Y;
        });
        b._resolved = true;
      }
    });
  }

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function animateBrush(b, startTime) {
    if (!b.brush || !b.stroke) return;
    resolvePaths();
    const pathStr = b._resolvedPath;
    if (!pathStr) return;

    const ns = 'http://www.w3.org/2000/svg';
    const measure = document.createElementNS(ns, 'svg');
    measure.setAttribute('width', '0');
    measure.setAttribute('height', '0');
    measure.style.position = 'absolute';
    measure.style.visibility = 'hidden';
    const p = document.createElementNS(ns, 'path');
    p.setAttribute('d', pathStr);
    measure.appendChild(p);
    document.body.appendChild(measure);
    const totalLen = p.getTotalLength();
    document.body.removeChild(measure);

    function frame(now) {
      const elapsed = now - startTime;
      if (elapsed < 0) {
        requestAnimationFrame(frame);
        return;
      }

      let t = b.duration > 0 ? Math.min(elapsed / b.duration, 1) : 1;
      const eased = easeInOutCubic(t);
      const pt = p.getPointAtLength(totalLen * eased);

      const ahead = Math.min(eased + 0.01, 1);
      const ptAhead = p.getPointAtLength(totalLen * ahead);
      const dx = ptAhead.x - pt.x;
      const dy = ptAhead.y - pt.y;
      const angle = Math.atan2(dy, dx) * (180 / Math.PI);

      const BRUSH_SIZE = 64;
      const tx = pt.x - BRUSH_SIZE / 2;
      const ty = pt.y - BRUSH_SIZE / 2;

      // フェードイン/アウトを線の進捗と同期
      let brushOpacity = 1;
      if (t < 0.08) brushOpacity = t / 0.08;
      else if (t > 0.88) brushOpacity = (1 - t) / 0.12;

      b.brush.style.opacity = brushOpacity;
      b.brush.style.transform = 'translate(' + tx + 'px,' + ty + 'px) rotate(' + angle + 'deg)';

      if (b.stroke) {
        b.stroke.style.opacity = '0.9';
        b.stroke.setAttribute('stroke-dasharray', totalLen);
        b.stroke.setAttribute('stroke-dashoffset', totalLen * (1 - eased));
        if (t >= 1 && !b.stroke.classList.contains('completed')) {
          b.stroke.classList.add('completed');
          b.stroke.classList.add('bleeding');
        }
      }

      if (t < 1) {
        requestAnimationFrame(frame);
      }
    }
    requestAnimationFrame(frame);
  }

  // 全筆を順次スタート（setTimeoutを1つに統合）
  brushes.forEach(b => {
    setTimeout(() => animateBrush(b, performance.now()), b.delay);
  });

  // リサイズ時にpath再計算（確定フラグを外す）
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      brushes.forEach(b => { b._resolved = false; });
    }, 150);
  });

  // prefers-reduced-motion
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('.ink-stroke').forEach(s => {
      s.style.transition = 'none';
      s.style.opacity = '0.85';
      const arr = s.getAttribute('stroke-dasharray');
      if (arr) s.style.strokeDashoffset = '0';
    });
    document.querySelectorAll('.ink-brush').forEach(b => b.style.display = 'none');
  }
})();
