const sampleScript = `雨夜，女主林晚站在医院走廊尽头，手里攥着一张亲子鉴定报告。

男主沈越从电梯里冲出来，西装被雨水打湿。他看见报告，停住脚步。

林晚低声说：你早就知道，对吗？

沈越没有回答，只看向病房门口。门内传来孩子微弱的咳嗽声。

林晚转身要走，沈越终于开口：如果我说，我一直在保护你呢？`;

const palettes = [
  ["#214b57", "#161716"],
  ["#6d3f33", "#211917"],
  ["#48624d", "#1d2220"],
  ["#33385c", "#12131d"],
  ["#7a5a25", "#1d1811"],
  ["#7a2e3a", "#201418"],
];

let shots = [];
let activeShotIndex = 0;
const MAX_SHOT_GRID = 9;

const storyInput = document.querySelector("#storyInput");
const styleSelect = document.querySelector("#styleSelect");
const ratioSelect = document.querySelector("#ratioSelect");
const shotGrid = document.querySelector("#shotGrid");
const timeline = document.querySelector("#timeline");
const promptOutput = document.querySelector("#promptOutput");
const exportOutput = document.querySelector("#exportOutput");
const activeShotId = document.querySelector("#activeShotId");
const activePreview = document.querySelector("#activePreview");

storyInput.value = sampleScript;

document.querySelector("#loadSample").addEventListener("click", () => {
  storyInput.value = sampleScript;
  generateStoryboard();
});

document.querySelector("#generateBtn").addEventListener("click", generateStoryboard);

document.querySelector("#copyJson").addEventListener("click", async () => {
  await navigator.clipboard.writeText(exportOutput.value);
});

document.querySelectorAll(".segmented button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".segmented button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    const isTimeline = button.dataset.view === "timeline";
    shotGrid.classList.toggle("hidden", isTimeline);
    timeline.classList.toggle("hidden", !isTimeline);
  });
});

document.querySelectorAll(".review-tags button").forEach((button) => {
  button.addEventListener("click", () => {
    if (!shots[activeShotIndex]) return;
    shots[activeShotIndex].revisionTags.push(button.dataset.tag);
    updateInspector();
    renderShots();
  });
});

function generateStoryboard() {
  const text = storyInput.value.trim();
  const paragraphs = text
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
  const limitedParagraphs = paragraphs.slice(0, MAX_SHOT_GRID);

  shots = limitedParagraphs.map((paragraph, index) => {
    const hasDialogue = /[：:]/.test(paragraph);
    const shotType = pickShotType(paragraph, index);
    const duration = hasDialogue ? 5 : index === 0 ? 4 : 3;
    const palette = palettes[index % palettes.length];
    return {
      id: `S${String(index + 1).padStart(2, "0")}`,
      title: inferTitle(paragraph, index),
      duration,
      framing: shotType.framing,
      camera: shotType.camera,
      action: paragraph,
      keyframeCount: 3,
      selectedFrame: 1,
      palette,
      revisionTags: [],
      prompt: buildPrompt(paragraph, shotType),
    };
  });

  activeShotIndex = 0;
  renderShots();
  renderTimeline();
  updateInspector();
}

function pickShotType(text, index) {
  if (/报告|手机|照片|合同|信/.test(text)) {
    return { framing: "特写", camera: "缓慢推进，焦点锁定手部道具" };
  }
  if (/冲|跑|转身|走/.test(text)) {
    return { framing: "中景", camera: "手持跟拍，轻微晃动" };
  }
  if (/[：:]/.test(text)) {
    return { framing: "近景", camera: "过肩镜头，浅景深" };
  }
  if (index === 0) {
    return { framing: "远景", camera: "静态建立镜头，低机位" };
  }
  return { framing: "中近景", camera: "横移，人物居中偏左" };
}

function inferTitle(text, index) {
  const clean = text.replace(/[：:]/g, " ").replace(/[，。！？,.!?]/g, " ");
  const words = clean.split(/\s+/).filter(Boolean);
  return words.slice(0, 8).join(" ") || `镜头 ${index + 1}`;
}

function buildPrompt(text, shotType) {
  return [
    ratioSelect.value,
    styleSelect.value,
    shotType.framing,
    shotType.camera,
    "consistent character identity, same face, same wardrobe, cinematic lighting",
    text,
    "clear emotional continuity, production storyboard keyframe, no text overlay",
  ].join(", ");
}

function renderShots() {
  const slots = Array.from({ length: MAX_SHOT_GRID }, (_, index) => {
    const shot = shots[index];
    if (!shot) {
      return `
        <article class="shot-card empty-slot">
          <div class="shot-body">
            <h3>空位</h3>
            <p>生成后自动补齐（最多 9 镜头）</p>
          </div>
        </article>
      `;
    }

    const frames = Array.from({ length: shot.keyframeCount })
      .map((_, frameIndex) => {
        const selected = shot.selectedFrame === frameIndex + 1 ? "selected" : "";
        return `<button class="mini-button ${selected}" type="button" data-shot="${index}" data-frame="${frameIndex + 1}">K${frameIndex + 1}</button>`;
      })
      .join("");

    return `
      <article class="shot-card ${index === activeShotIndex ? "active" : ""}" data-shot="${index}">
        <div class="frame-strip">
          ${[0, 1, 2]
            .map(
              () => `
                <div class="frame" style="--frame-a:${shot.palette[0]}; --frame-b:${shot.palette[1]}" aria-hidden="true"></div>
              `
            )
            .join("")}
        </div>
        <div class="shot-body">
          <div class="shot-meta">
            <span>${shot.id} / ${shot.duration}s</span>
            <span>${shot.framing}</span>
          </div>
          <h3>${escapeHtml(shot.title)}</h3>
          <p>${escapeHtml(shot.camera)}</p>
          <div class="shot-actions">${frames}</div>
        </div>
      </article>
    `;
  });

  shotGrid.innerHTML = slots.join("");

  document.querySelectorAll(".shot-card[data-shot]").forEach((card) => {
    card.addEventListener("click", () => {
      activeShotIndex = Number(card.dataset.shot);
      renderShots();
      renderTimeline();
      updateInspector();
    });
  });

  document.querySelectorAll(".mini-button").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const shotIndex = Number(button.dataset.shot);
      shots[shotIndex].selectedFrame = Number(button.dataset.frame);
      activeShotIndex = shotIndex;
      renderShots();
      updateInspector();
    });
  });

  updateCounters();
}

function renderTimeline() {
  timeline.innerHTML = shots
    .map((shot, index) => {
      const width = Math.max(18, shot.duration * 12);
      return `
        <button class="timeline-row" type="button" data-shot="${index}">
          <strong>${shot.id}</strong>
          <span class="timeline-bar" style="width:${width}%"></span>
          <span>${shot.duration}s</span>
        </button>
      `;
    })
    .join("");

  document.querySelectorAll(".timeline-row").forEach((row) => {
    row.addEventListener("click", () => {
      activeShotIndex = Number(row.dataset.shot);
      renderShots();
      updateInspector();
    });
  });
}

function updateInspector() {
  const shot = shots[activeShotIndex];
  if (!shot) {
    activeShotId.textContent = "--";
    promptOutput.value = "";
    exportOutput.value = "";
    return;
  }

  const revision = shot.revisionTags.length
    ? `, revision notes: ${shot.revisionTags.join(" / ")}`
    : "";

  activeShotId.textContent = `${shot.id} / K${shot.selectedFrame}`;
  promptOutput.value = `${shot.prompt}${revision}`;
  activePreview.style.background = `linear-gradient(150deg, rgba(255,255,255,.22), transparent 34%), linear-gradient(180deg, ${shot.palette[0]}, ${shot.palette[1]} 72%)`;
  exportOutput.value = JSON.stringify(
    {
      project: "AI 短剧关键帧分镜台",
      style: styleSelect.value,
      ratio: ratioSelect.value,
      shots: shots.map((item) => ({
        id: item.id,
        duration: item.duration,
        framing: item.framing,
        camera: item.camera,
        action: item.action,
        selected_keyframe: `K${item.selectedFrame}`,
        prompt: item.prompt,
        revision_tags: item.revisionTags,
      })),
    },
    null,
    2
  );
  updateCounters();
}

function updateCounters() {
  document.querySelector("#shotCount").textContent = shots.length;
  document.querySelector("#frameCount").textContent = shots.reduce((sum, shot) => sum + shot.keyframeCount, 0);
  document.querySelector("#riskCount").textContent = shots.filter((shot) => shot.revisionTags.length > 0).length;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

generateStoryboard();
