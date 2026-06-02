const genrePrompts = {
  "都市悬疑": [
    "夜市拐角传来争执声，主角拿到一段关键线索后被警告要闭嘴。",
    "主角与搭档在电梯里低声对话，时间戳被刻意修改。",
    "雨夜天台对峙，真凶试图抹去证据，主角反杀反杀。",
    "警笛远处闪烁，真相在监控与账本里重合。",
  ],
  "现实情感": [
    "公交车上，女主被短信惊到，尴尬地在下一个站下车。",
    "餐馆包厢里，沉默的晚餐让误会比语言更重。",
    "雨中的便利店门前，男主递出一张旧票据，两人沉默。",
    "晨光里的一通语音回放，让关系在一句“对不起”后有了转机。",
  ],
  "古风权谋": [
    "宫灯摇曳，内库账册被悄悄换过，太子仓皇下令封城。",
    "偏厅中，侍女与公主在暗格夹缝里交换密信。",
    "朝堂上翻案时，主角以旧誓书逼迫权臣现身。",
    "月下回程路上，盟约被破，刀光照亮旧誓词。",
  ],
  "科幻冒险": [
    "宇宙港检修舱里，主角发现能源核心被远程替换。",
    "城市上空出现干扰波，AR 地图突然只剩一条逃生线。",
    "废弃地铁站中，飞船通讯片刻恢复，敌我双方都在听。",
    "终端端口开启，团队以旧规则破解最后一层防火墙。",
  ],
};

const sampleIdea = `高压电梯里，女主手里拿着一张拍糊的监控照片。她看到照片里出现自己失踪已久的弟弟。只要把照片交给记者，真相会全被知道。`

let scenes = [];
let activeSceneIndex = 0;
let currentCastCount = 2;

const storyInput = document.querySelector("#storyInput");
const genreSelect = document.querySelector("#genreSelect");
const durationSelect = document.querySelector("#durationSelect");
const castSelect = document.querySelector("#castSelect");
const styleSelect = document.querySelector("#styleSelect");
const shotGrid = document.querySelector("#shotGrid");
const scriptOutput = document.querySelector("#scriptOutput");
const exportOutput = document.querySelector("#exportOutput");
const activeShotId = document.querySelector("#activeShotId");
const sceneBadge = document.querySelector("#sceneBadge");

storyInput.value = sampleIdea;

document.querySelector("#loadSample").addEventListener("click", () => {
  storyInput.value = sampleIdea;
  generateScript();
});

document.querySelector("#generateBtn").addEventListener("click", generateScript);

document.querySelector("#copyScript").addEventListener("click", async () => {
  await navigator.clipboard.writeText(scriptOutput.value);
});

document.querySelector("#copyJson").addEventListener("click", async () => {
  await navigator.clipboard.writeText(exportOutput.value);
});

document.querySelector("#downloadScript").addEventListener("click", () => {
  const blob = new Blob([scriptOutput.value || ""], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "short_drama_script.txt";
  anchor.click();
  URL.revokeObjectURL(url);
});

function generateScript() {
  const idea = storyInput.value.trim();
  const genre = genreSelect.value;
  const targetLength = Number(durationSelect.value.replace(/\D/g, ""));
  const castCount = parseCastCount(castSelect.value);
  const styleTone = styleSelect.value;
  currentCastCount = castCount;

  const basePool = genrePrompts[genre] || genrePrompts["都市悬疑"];
  const beats = [
    "开场钩子",
    "冲突抛出",
    "信息逆转",
    "对抗反击",
    "情绪反转",
    "收束转场",
  ];

  const totalScenes = Math.max(5, Math.min(9, Math.round(targetLength / 20)));
  scenes = beats.slice(0, totalScenes).map((beat, index) => {
    const promptPool = basePool[index % basePool.length];
    const sceneSec = Math.max(6, Math.round(targetLength / totalScenes));
    return {
      id: `SCN-${String(index + 1).padStart(2, "0")}`,
      title: `${beat}：${idea.split(/[,。！？.!]/)[0] || "主线触发"}`,
      duration: `${sceneSec}秒`,
      location: chooseLocation(index, genre),
      characterCount: castCount,
      conflict: promptPool,
      dialogue: `${idea}${beat === "情绪反转" ? "，但真相并未改变。" : "，局势瞬间失控。"}`,
      style: styleTone,
      beat,
    };
  });

  activeSceneIndex = 0;
  renderSceneCards();
  updateOutput();
}

function chooseLocation(index, genre) {
  const locByGenre = {
    "都市悬疑": ["旧仓库", "地下停车场", "医院走廊", "夜市巷口"],
    "现实情感": ["快餐店", "旧楼天台", "出租屋", "巴士站"],
    "古风权谋": ["偏殿", "内库", "后花园", "护城河旁"],
    "科幻冒险": ["宇宙货仓", "地下发射井", "废弃站厅", "海面平台"],
  };
  const arr = locByGenre[genre] || locByGenre["都市悬疑"];
  return arr[index % arr.length];
}

function renderSceneCards() {
  shotGrid.innerHTML = scenes
    .map((scene, index) => {
      const active = index === activeSceneIndex ? "active" : "";
      return `
        <article class="shot-card ${active}" data-scene="${index}">
          <div class="shot-body">
            <div class="shot-meta">
              <span>${scene.id}</span>
              <span>${scene.duration}</span>
            </div>
            <h3>${escapeHtml(scene.title)}</h3>
            <p class="scene-location">地点：${escapeHtml(scene.location)} / 人物 ${scene.characterCount} 人</p>
            <p>${escapeHtml(scene.conflict)}</p>
            <button class="mini-button" type="button" data-scene="${index}">编辑预览</button>
          </div>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll(".shot-card").forEach((card) => {
    card.addEventListener("click", () => {
      activeSceneIndex = Number(card.dataset.scene);
      renderSceneCards();
      updateOutput();
    });
  });

  sceneBadge.textContent = `${scenes.length} 个场景已生成`;
}

function updateOutput() {
  if (!scenes.length) {
    scriptOutput.value = "点击“生成短剧脚本”生成内容。";
    exportOutput.value = JSON.stringify({
      title: `${genreSelect.value}短剧脚本`,
      duration: durationSelect.value,
      style: styleSelect.value,
      genre: genreSelect.value,
      castCount: currentCastCount,
      scenes: [],
    }, null, 2);
    activeShotId.textContent = "--";
    document.querySelector("#sceneCount").textContent = 0;
    document.querySelector("#wordCount").textContent = 0;
    document.querySelector("#lengthCount").textContent = 0;
    return;
  }

  const lines = scenes.map((scene, index) => {
    const sceneIndex = index + 1;
    return `
【场景 ${sceneIndex}】
地点：${scene.location}
时长：${scene.duration}
镜头节奏：${scene.beat}
人物：${scene.characterCount} 人
旁白：${scene.style}
台词/动作：${scene.dialogue}
`.trim();
  });

  scriptOutput.value = lines.join("\n\n");
  exportOutput.value = JSON.stringify({
    title: `${genreSelect.value}短剧脚本`,
    duration: durationSelect.value,
    style: styleSelect.value,
    genre: genreSelect.value,
    castCount: currentCastCount,
    scenes,
  }, null, 2);

  const activeScene = scenes[activeSceneIndex];
  if (activeScene) {
    activeShotId.textContent = `${activeScene.id} · ${activeScene.location}`;
  } else {
    activeShotId.textContent = "--";
  }

  const totalWords = scriptOutput.value.length;
  const totalDuration = scenes.reduce((sum, scene) => sum + Number(scene.duration.replace(/\D/g, "")), 0);
  document.querySelector("#sceneCount").textContent = scenes.length;
  document.querySelector("#wordCount").textContent = totalWords;
  document.querySelector("#lengthCount").textContent = totalDuration;
}

function parseCastCount(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : 2;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// 首屏展示
generateScript();
