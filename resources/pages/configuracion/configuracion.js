(function () {
  "use strict";
  const card = document.querySelector(".card");
  const ssidInput = document.getElementById("ssid");
  const ssidLen = document.getElementById("ssid-len");
  const passInput = document.getElementById("password");
  const toggleBtn = document.getElementById("togglePass");
  const eyeOn = toggleBtn.querySelector(".icon-eye");
  const eyeOff = toggleBtn.querySelector(".icon-eye-off");
  const strengthBox = document.getElementById("strengthBox");
  const strengthFill = document.getElementById("strengthFill");
  const strengthLbl = document.getElementById("strengthLabel");
  const canvas = document.getElementById("bgCanvas");
  const ctx = canvas.getContext("2d");
  let W, H, particles = [];
  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  function makeParticle() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.2 + 0.3,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      a: Math.random() * 0.5 + 0.1,
    };
  }
  function initParticles(n = 70) {
    particles = Array.from({ length: n }, makeParticle);
  }
  function drawParticles() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = W;
      if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H;
      if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(184,255,60,${p.a})`;
      ctx.fill();
    });
    requestAnimationFrame(drawParticles);
  }
  resize();
  initParticles();
  drawParticles();
  window.addEventListener("resize", () => { resize(); initParticles(); });
  [ssidInput, passInput].forEach(el => {
    el.addEventListener("focus", () => card.classList.add("card--active"));
    el.addEventListener("blur", () => {
      if (document.activeElement !== ssidInput && document.activeElement !== passInput)
        card.classList.remove("card--active");
    });
  });
  function updateSsidLen() {
    const n = ssidInput.value.length;
    ssidLen.textContent = n;
    ssidLen.classList.toggle("hi", n >= 28);
  }
  ssidInput.addEventListener("input", updateSsidLen);
  updateSsidLen();
  toggleBtn.addEventListener("click", () => {
    const show = passInput.type === "password";
    passInput.type = show ? "text" : "password";
    eyeOn.style.display = show ? "none" : "";
    eyeOff.style.display = show ? "" : "none";
    toggleBtn.setAttribute("aria-label", show ? "Ocultar contraseña" : "Mostrar contraseña");
  });
  const levels = [
    { pct: 0, color: "#3A4558", label: "" },
    { pct: 20, color: "#FF4F6A", label: "MUY DÉBIL" },
    { pct: 40, color: "#FFAD3B", label: "DÉBIL" },
    { pct: 60, color: "#FFE566", label: "REGULAR" },
    { pct: 80, color: "#B8FF3C", label: "BUENA" },
    { pct: 100, color: "#3BFFB0", label: "EXCELENTE" },
  ];
  function scorePassword(p) {
    if (!p.length) return 0;
    let s = 0;
    if (p.length >= 8) s++;
    if (p.length >= 12) s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[0-9]/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    return s;
  }
  passInput.addEventListener("input", () => {
    const val = passInput.value;
    const score = scorePassword(val);
    const lv = levels[score];
    if (val.length > 0) {
      strengthBox.classList.add("visible");
      strengthFill.style.width = lv.pct + "%";
      strengthFill.style.background = lv.color;
      strengthLbl.textContent = lv.label;
      strengthLbl.style.color = lv.color;
    } else {
      strengthBox.classList.remove("visible");
    }
  });
})();