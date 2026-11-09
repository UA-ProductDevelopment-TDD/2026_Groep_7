/* Canvas terrain renderer: no network or robot commands. */
(function() {
  const C = BittleCore;

  function rr(c, x, y, w, h, r, fill, stroke) {
    c.beginPath();
    c.roundRect(x, y, w, h, r);
    if (fill) {
      c.fillStyle = fill;
      c.fill();
    }
    if (stroke) {
      c.strokeStyle = stroke;
      c.stroke();
    }
  }

  function ellipse(c, x, y, rx, ry, color) {
    c.beginPath();
    c.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
    c.fillStyle = color;
    c.fill();
  }

  function line(c, points, color, width = 1) {
    if (!points.length) return;
    c.beginPath();
    c.moveTo(points[0].x, points[0].y);
    for (const p of points.slice(1)) c.lineTo(p.x, p.y);
    c.strokeStyle = color;
    c.lineWidth = width;
    c.stroke();
  }
  class TerrainView {
    constructor(canvas, getData, options = {}) {
      this.canvas = canvas;
      this.c = canvas.getContext('2d');
      this.getData = getData;
      this.options = options;
      this.zoom = 1;
      this.selected = null;
      this.draft = [];
      this.samples = [];
      this.lastTrail = 0;
      this.running = true;
      this.base = document.createElement('canvas');
      this.base.width = 960;
      this.base.height = 600;
      this.mask = document.createElement('canvas');
      this.mask.width = 480;
      this.mask.height = 300;
      this.trail = document.createElement('canvas');
      this.trail.width = 480;
      this.trail.height = 300;
      this.resize = new ResizeObserver(() => this.fit());
      this.resize.observe(canvas);
      this.dirty = true;
      this.loop = t => {
        if (!this.running) return;
        this.draw(t);
        this.raf = requestAnimationFrame(this.loop);
      };
      this.fit();
      this.raf = requestAnimationFrame(this.loop);
    }
    destroy() {
      this.running = false;
      cancelAnimationFrame(this.raf);
      this.resize.disconnect();
    }
    fit() {
      const box = this.canvas.getBoundingClientRect(),
        dpr = Math.min(devicePixelRatio || 1, 2);
      this.canvas.width = Math.max(1, Math.round(box.width * dpr));
      this.canvas.height = Math.max(1, Math.round(box.height * 600 / 960 * dpr));
    }
    point(e) {
      const r = this.canvas.getBoundingClientRect();
      return {
        x: 480 + ((e.clientX - r.left) * 960 / r.width - 480) / this.zoom,
        y: 300 + ((e.clientY - r.top) * 600 / r.height - 300) / this.zoom
      };
    }
    invalidate() {
      this.dirty = true;
    }
    terrain() {
      const c = this.base.getContext('2d');
      c.clearRect(0, 0, 960, 600);
      const g = c.createLinearGradient(0, 0, 960, 600);
      g.addColorStop(0, '#e8ecdf');
      g.addColorStop(1, '#d5dfc5');
      c.fillStyle = g;
      c.fillRect(0, 0, 960, 600);
      c.save();
      rr(c, 42, 38, 876, 520, 25, '#dae3ca');
      c.clip();
      for (let x = -400; x < 1100; x += 90) {
        c.fillStyle = '#ffffff13';
        c.beginPath();
        c.moveTo(x, 0);
        c.lineTo(x + 45, 0);
        c.lineTo(x + 445, 600);
        c.lineTo(x + 400, 600);
        c.fill();
      }
      let seed = 71;
      for (let i = 0; i < 4800; i++) {
        seed = (seed * 16807) % 2147483647;
        const x = seed % 960;
        seed = (seed * 16807) % 2147483647;
        const y = seed % 600;
        c.fillStyle = i % 2 ? '#71835b0e' : '#fff8e815';
        c.fillRect(x, y, 1.2, 2.4);
      }
      c.restore();
      c.shadowColor = '#29382018';
      c.shadowBlur = 7;
      c.shadowOffsetY = 3;
      rr(c, 35, 32, 890, 532, 29, null, '#9da991');
      c.shadowBlur = 0;
      c.shadowOffsetY = 0;
      c.lineWidth = 5;
      rr(c, 39, 36, 882, 524, 26, null, '#f8f7eb');
      c.lineWidth = 1;
      for (let x = 65; x < 910; x += 27) {
        rr(c, x, 30, 5, 11, 1, '#9ca58d');
        rr(c, x, 557, 5, 11, 1, '#9ca58d');
      }
      for (let y = 67; y < 545; y += 27) {
        rr(c, 32, y, 10, 5, 1, '#9ca58d');
        rr(c, 918, y, 10, 5, 1, '#9ca58d');
      }
      rr(c, 70, 505, 185, 34, 4, '#d2cdbc');
      for (let x = 72; x < 255; x += 23) {
        c.strokeStyle = '#eeebdd';
        c.beginPath();
        c.moveTo(x, 505);
        c.lineTo(x, 539);
        c.stroke();
      }
      c.fillStyle = '#7e8e7020';
      c.font = '600 11px Segoe UI';
      c.fillText('TUIN', 65, 78);
      for (const z of this.getData().zones) {
        c.beginPath();
        z.points.forEach((p, i) => i ? c.lineTo(p.x, p.y) : c.moveTo(p.x, p.y));
        c.closePath();
        c.fillStyle = '#bb775522';
        c.fill();
        c.strokeStyle = '#ad795c';
        c.setLineDash([5, 5]);
        c.stroke();
        c.setLineDash([]);
      }
      this.dirty = false;
    }
    object(c, o, t) {
      c.save();
      c.translate(o.x, o.y);
      c.rotate(o.rotation * Math.PI / 180);
      c.shadowColor = '#28351e26';
      c.shadowBlur = 12;
      c.shadowOffsetY = 7;
      const w = o.w,
        h = o.h;
      if (o.type === 'coop') {
        rr(c, -w / 2 - 6, -h / 2 - 5, w + 12, h + 10, 4, '#b4b09b');
        c.shadowBlur = 0;
        c.shadowOffsetY = 0;
        const a = c.createLinearGradient(-w / 2, 0, w / 2, 0);
        a.addColorStop(0, '#7e8d78');
        a.addColorStop(.49, '#b4bf9f');
        a.addColorStop(.5, '#6c7b65');
        a.addColorStop(1, '#849373');
        rr(c, -w / 2, -h / 2, w, h, 2, a);
        c.strokeStyle = '#eff0da40';
        c.lineWidth = 1;
        for (let y = -h / 2 + 7; y < h / 2; y += 8) {
          c.beginPath();
          c.moveTo(-w / 2, y);
          c.lineTo(w / 2, y);
          c.stroke();
        }
        rr(c, -2, -h / 2 - 2, 4, h + 4, 1, '#d2d7bd');
        rr(c, -w / 2 + 15, -h / 2 + 14, 27, 22, 2, '#495b4e', '#b1c2b1');
        c.strokeStyle = '#c5d0bb';
        c.beginPath();
        c.moveTo(-w / 2 + 28, -h / 2 + 14);
        c.lineTo(-w / 2 + 28, -h / 2 + 36);
        c.stroke();
      }
      if (o.type === 'plant') {
        ellipse(c, 0, 0, w * .48, h * .44, '#738c5c');
        c.shadowBlur = 0;
        c.shadowOffsetY = 0;
        for (let i = 0; i < 19; i++) {
          const a = i * 2.399,
            r = (i % 4) / 4 * w * .35;
          const color = ['#809b65', '#91ab75', '#6d8957', '#a0b583'][i % 4];
          ellipse(c, Math.cos(a) * r, Math.sin(a) * r, w * (.12 + (i % 3) * .015), h * .14, color);
        }
        ellipse(c, -w * .12, -h * .13, w * .12, h * .10, '#b3c59488');
      }
      if (o.type === 'water') {
        ellipse(c, 0, 0, w / 2, h / 2, '#b8b5a4');
        c.shadowBlur = 0;
        c.shadowOffsetY = 0;
        ellipse(c, 0, -2, w * .42, h * .4, '#527d7e');
        const g = c.createRadialGradient(-6, -6, 1, 0, 0, w * .4);
        g.addColorStop(0, '#b5d7cb');
        g.addColorStop(1, '#7aa4a0');
        ellipse(c, 0, -2, w * .35, h * .33, g);
        c.strokeStyle = '#d9eee0aa';
        c.beginPath();
        c.ellipse(0, -2, w * .22, h * .20, 0, .3, 2.6);
        c.stroke();
      }
      if (o.type === 'nest') {
        rr(c, -w / 2, -h / 2, w, h, 4, '#b89565');
        c.shadowBlur = 0;
        rr(c, -w * .42, -h * .4, w * .84, h * .8, 3, '#d7bd89');
        for (let i = 0; i < 9; i++) {
          c.strokeStyle = '#af8d5866';
          c.beginPath();
          c.moveTo(-w * .3 + i * 3, -h * .3);
          c.lineTo(-w * .2 + i * 3, h * .3);
          c.stroke();
        }
        for (let i = 0; i < Math.min(this.getData().eggs, 4); i++) ellipse(c, -w * .22 + i * w * .14, 0, 4, 6, '#f3e5c8');
      }
      if (o.type === 'dock') {
        rr(c, -w / 2, -h / 2, w, h, 6, '#586353');
        c.shadowBlur = 0;
        c.shadowOffsetY = 0;
        rr(c, -w * .39, -h * .3, w * .78, h * .6, 4, '#303e33');
        rr(c, -w * .28, -h * .24, 4, h * .48, 1, '#bbc4ad');
        rr(c, w * .21, -h * .24, 4, h * .48, 1, '#bbc4ad');
        ellipse(c, 0, -h * .38, 2.3, 2.3, '#a5d38b');
      }
      if (o.type === 'fence') {
        rr(c, -w / 2, -h / 2, w, h, 1, '#b2a689');
        c.shadowBlur = 0;
        rr(c, -w / 2, -h / 2, w, 3, 1, '#e3d7b7');
        for (let x = -w / 2; x < w / 2; x += 18) rr(c, x, -h / 2 - 3, 4, h + 6, 1, '#817b63');
      }
      if (o.type === 'door') {
        rr(c, -w / 2, -h / 2, w, h, 1, '#af9467');
        c.shadowBlur = 0;
        for (let x = -w / 2 + 4; x < w / 2; x += 7) rr(c, x, -h / 2, 2, h, 0, '#dec594');
        ellipse(c, w * .36, 0, 2, 2, '#43553a');
      }
      c.shadowBlur = 0;
      c.shadowOffsetY = 0;
      if (this.selected === o.id) {
        c.strokeStyle = '#344e3d';
        c.lineWidth = 1.5;
        c.setLineDash([4, 3]);
        rr(c, -w / 2 - 10, -h / 2 - 10, w + 20, h + 20, 5, null, '#344e3d');
        c.setLineDash([]);
        for (const x of [-w / 2 - 10, w / 2 + 10])
          for (const y of [-h / 2 - 10, h / 2 + 10]) rr(c, x - 3, y - 3, 6, 6, 1, 'white', '#344e3d');
      }
      c.restore();
    }
    makeTrail(t) {
      if (t - this.lastTrail < 85) return;
      this.lastTrail = t;
      this.samples = this.samples.filter(p => t - p.t < 120000);
      const m = this.mask.getContext('2d', {
        willReadFrequently: true
      });
      m.fillStyle = 'black';
      m.fillRect(0, 0, 480, 300);
      m.globalCompositeOperation = 'lighten';
      m.lineCap = 'round';
      m.lineJoin = 'round';
      m.lineWidth = 32;
      for (let i = 1; i < this.samples.length; i++) {
        const a = this.samples[i - 1],
          b = this.samples[i];
        if (b.break) continue;
        const alpha = p => Math.round(255 * Math.pow(Math.max(0, 1 - (t - p.t) / 120000), 1.3));
        const g = m.createLinearGradient(a.x / 2, a.y / 2, b.x / 2, b.y / 2);
        const aa = alpha(a),
          bb = alpha(b);
        g.addColorStop(0, `rgb(${aa},${aa},${aa})`);
        g.addColorStop(1, `rgb(${bb},${bb},${bb})`);
        m.strokeStyle = g;
        m.beginPath();
        m.moveTo(a.x / 2, a.y / 2);
        m.lineTo(b.x / 2, b.y / 2);
        m.stroke();
      }
      m.globalCompositeOperation = 'source-over';
      const im = m.getImageData(0, 0, 480, 300);
      for (let i = 0; i < im.data.length; i += 4) {
        const a = im.data[i];
        im.data[i] = 108;
        im.data[i + 1] = 151;
        im.data[i + 2] = 75;
        im.data[i + 3] = a * .36;
      }
      this.trail.getContext('2d').putImageData(im, 0, 0);
    }
    draw(t) {
      if (!this.canvas.width) return;
      if (this.dirty) this.terrain();
      const c = this.c;
      c.setTransform(this.canvas.width / 960, 0, 0, this.canvas.height / 600, 0, 0);
      c.clearRect(0, 0, 960, 600);
      c.save();
      c.translate(480, 300);
      c.scale(this.zoom, this.zoom);
      c.translate(-480, -300);
      c.drawImage(this.base, 0, 0);
      this.makeTrail(t);
      c.save();
      c.filter = 'blur(5px)';
      c.drawImage(this.trail, 0, 0, 960, 600);
      c.restore();
      const data = this.getData();
      if (this.options.editor) {
        for (const r of data.routes) {
          c.save();
          c.setLineDash([5, 6]);
          line(c, r.closed ? [...r.points, r.points[0]] : r.points, '#73935c', 2);
          c.restore();
          for (const [i, p] of r.points.entries()) {
            ellipse(c, p.x, p.y, 5, 5, '#fffef7');
            c.strokeStyle = '#61854e';
            c.stroke();
            if (this.selected === r.id) {
              c.fillStyle = '#35532c';
              c.font = '10px Segoe UI';
              c.fillText(i + 1, p.x + 9, p.y - 7);
            }
          }
        }
      }
      for (const o of data.objects) this.object(c, o, t);
      if (this.options.editor && this.draft.length) {
        line(c, this.draft, '#b27b42', 2);
        for (const p of this.draft) ellipse(c, p.x, p.y, 4, 4, '#b27b42');
      }
      const r = this.options.robot?.();
      if (r) {
        c.save();
        c.translate(r.x, r.y);
        c.rotate(r.heading || 0);
        const cone = c.createRadialGradient(0, 0, 0, 0, 0, 100);
        cone.addColorStop(0, '#8dad6c40');
        cone.addColorStop(1, '#8dad6c00');
        c.beginPath();
        c.moveTo(0, 0);
        c.arc(0, 0, 100, -.48, .48);
        c.closePath();
        c.fillStyle = cone;
        c.fill();
        c.shadowColor = '#26381f44';
        c.shadowBlur = 10;
        c.shadowOffsetY = 5;
        const phase = r.moving ? Math.sin(t * .014) * 3 : 0;
        for (const x of [-10, 9])
          for (const y of [-12, 12]) rr(c, x - 3 + (y < 0 ? phase : -phase), y - 3, 8, 6, 2, '#44503b');
        rr(c, -16, -10, 29, 20, 6, '#e7dfba', '#b4ad8d');
        c.shadowBlur = 0;
        c.shadowOffsetY = 0;
        rr(c, -9, -7, 18, 14, 3, '#4d5c42');
        rr(c, 12, -8, 10, 16, 4, '#d5c793', '#8d8668');
        rr(c, 19, -5, 3, 10, 1, '#29382b');
        ellipse(c, -8, 0, 2, 2, '#b3d89c');
        c.restore();
      }
      c.fillStyle = '#637358';
      c.font = '11px Segoe UI';
      c.fillText('N', 878, 87);
      line(c, [{
        x: 882,
        y: 100
      }, {
        x: 882,
        y: 113
      }], '#637358');
      c.restore();
    }
  }
  window.TerrainView = TerrainView;
})();
