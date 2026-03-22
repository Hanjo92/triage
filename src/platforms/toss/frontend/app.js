const API_BASE = "";

// Telegram WebApp 객체 연동
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand(); // 텔레그램 안에서 화면 꽉 차게 확장
}

let appState = {
  // 텔레그램 프로필이 있으면 해당 ID를, 없으면 토스용 임시 ID 사용
  userId: (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) 
          ? tg.initDataUnsafe.user.id.toString() 
          : "toss_user_" + Math.floor(Math.random() * 1000000),
  energy: null,
  time: null,
  state: null,
  candidates: [],
  selectedAction: null,
  score: 0
};

const appContainer = document.getElementById("app-container");

// Render Utilities
const clearView = () => {
  appContainer.innerHTML = "";
};

const createElem = (tag, className, innerHTML) => {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (innerHTML) el.innerHTML = innerHTML;
  return el;
};

// --- Views ---

const renderSplash = async () => {
  clearView();
  // Fetch streak info
  try {
    const res = await fetch(`${API_BASE}/v1/streaks/today?user_id=${appState.userId}`);
    if (res.ok) {
      const data = await res.json();
      const badge = document.getElementById("streak-badge");
      document.getElementById("streak-days").innerText = data.missed_days === 0 ? "순항중" : `누락 ${data.missed_days}`;
      if (data.missed_days >= 0) badge.classList.remove("hidden");
    }
  } catch (e) {
    console.error("Streak fetch error", e);
  }

  const view = createElem("div", "view");
  view.appendChild(createElem("h1", "title", "굿모닝!☀️<br/>오늘 아침을 어떻게<br/>시작해볼까요?"));
  view.appendChild(createElem("p", "subtitle", "트리아지가 가벼운 미션을 추천해 드려요."));

  const btnContainer = createElem("div", "options-list");
  
  const startBtn = createElem("button", "btn primary", "10초 체크인 시작 ➔");
  startBtn.onclick = () => renderEnergyCheck();
  btnContainer.appendChild(startBtn);
  view.appendChild(btnContainer);

  appContainer.appendChild(view);
};

const renderEnergyCheck = () => {
  clearView();
  const view = createElem("div", "view");
  view.appendChild(createElem("h1", "title", "현재 몸 상태(에너지)는<br/>어떤가요?"));

  const options = [
    { label: "🙂 가벼운 편이에요", val: "high" },
    { label: "😐 그냥 보통이에요", val: "mid" },
    { label: "😵 완전 방전됐어요", val: "low" }
  ];

  const list = createElem("div", "options-list");
  options.forEach(opt => {
    const btn = createElem("button", "btn", `<span>${opt.label}</span>`);
    btn.onclick = () => { appState.energy = opt.val; renderTimeCheck(); };
    list.appendChild(btn);
  });

  view.appendChild(list);
  appContainer.appendChild(view);
};

const renderTimeCheck = () => {
  clearView();
  const view = createElem("div", "view");
  view.appendChild(createElem("h1", "title", "지금 당장 가볍게<br/>투자할 수 있는 시간은요?"));

  const options = [
    { label: "⏱ 딱 3분", val: "3" },
    { label: "⏱ 10분 정도", val: "10" },
    { label: "⏱ 30분 이상 여유", val: "30" }
  ];

  const list = createElem("div", "options-list");
  options.forEach(opt => {
    const btn = createElem("button", "btn", `<span>${opt.label}</span>`);
    btn.onclick = () => { appState.time = opt.val; renderStateCheck(); };
    list.appendChild(btn);
  });

  view.appendChild(list);
  appContainer.appendChild(view);
};

const renderStateCheck = () => {
  clearView();
  const view = createElem("div", "view");
  view.appendChild(createElem("h1", "title", "마지막으로,<br/>현재 멘탈 및 기분은요?"));

  const options = [
    { label: "🤔 집중 잘 풀림", val: "focused" },
    { label: "🌀 약간 산만함", val: "distracted" },
    { label: "💦 스트레스/압박감", val: "stressed" },
    { label: "💤 그냥 지침", val: "tired" }
  ];

  const list = createElem("div", "options-list");
  options.forEach(opt => {
    const btn = createElem("button", "btn", `<span>${opt.label}</span>`);
    btn.onclick = () => { appState.state = opt.val; submitCheckin(); };
    list.appendChild(btn);
  });

  view.appendChild(list);
  appContainer.appendChild(view);
};

const renderLoading = () => {
  clearView();
  const loader = createElem("div", "loader-container");
  loader.appendChild(createElem("div", "spinner"));
  loader.appendChild(createElem("p", "subtitle", "최적의 행동 추천 중..."));
  appContainer.appendChild(loader);
};

const submitCheckin = async () => {
  renderLoading();
  try {
    const res = await fetch(`${API_BASE}/v1/checkins`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: appState.userId,
        energy_level: appState.energy,
        available_time: appState.time,
        mental_state: appState.state
      })
    });
    if (!res.ok) throw new Error("API FAILED");
    const data = await res.json();
    appState.candidates = data.action_candidates;
    renderRecommendation(data.message);
  } catch (err) {
    console.error(err);
    alert("서버 연결에 실패했습니다.");
    renderSplash();
  }
};

const renderRecommendation = (msgText) => {
  clearView();
  const view = createElem("div", "view");
  view.appendChild(createElem("p", "subtitle", msgText));
  
  if (appState.candidates.length > 0) {
    const hr = createElem("h1", "title", "이 중 하나만 골라보세요");
    view.appendChild(hr);
  }

  const list = createElem("div", "options-list");
  list.style.marginTop = "0";

  appState.candidates.forEach(act => {
    const card = createElem("div", "action-card");
    card.innerHTML = `<div class="action-card-title">${act.label}</div><div class="action-card-desc">${act.prompt_copy}</div>`;
    card.onclick = () => {
      appState.selectedAction = act;
      renderActionConfirm();
    };
    list.appendChild(card);
  });

  view.appendChild(list);
  
  // 패스 버튼
  const skipBtn = createElem("button", "btn secondary", "다음에 할게요");
  skipBtn.onclick = () => renderSplash();
  view.appendChild(skipBtn);
  
  appContainer.appendChild(view);
};

const renderActionConfirm = () => {
  clearView();
  const view = createElem("div", "view");
  view.appendChild(createElem("p", "subtitle", "미션 진행 중 🏃🏻"));
  view.appendChild(createElem("h1", "title", appState.selectedAction.prompt_copy));

  view.appendChild(createElem("p", "subtitle", "행동을 마친 뒤, 솔직한 결과를 알려주세요."));

  const list = createElem("div", "options-list");
  
  [
    { text: "✅ 끝까지 완료!", val: "done", class: "btn primary" },
    { text: "👌 조금 시도함", val: "partial", class: "btn" },
    { text: "❌ 결국 못함", val: "fail", class: "btn" }
  ].forEach(opt => {
    const b = createElem("button", opt.class, opt.text);
    b.onclick = () => submitCompletion(opt.val);
    list.appendChild(b);
  });

  view.appendChild(list);
  appContainer.appendChild(view);
};

const submitCompletion = async (status) => {
  renderLoading();
  try {
    const res = await fetch(`${API_BASE}/v1/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: appState.userId,
        action_id: appState.selectedAction.action_id,
        status: status
      })
    });
    if (!res.ok) throw new Error("API FAILED");
    const data = await res.json();
    renderResult(data.streak_message, data.score);
  } catch (err) {
    console.error(err);
    alert("기록 저장에 실패했습니다.");
    renderSplash();
  }
};

const renderResult = (message, score) => {
  clearView();
  const view = createElem("div", "view");
  view.appendChild(createElem("h1", "title", message));
  view.appendChild(createElem("p", "subtitle", `획득한 소프트 스트릭: +${score}점`));

  const list = createElem("div", "options-list");
  const homeBtn = createElem("button", "btn primary", "홈으로 돌아가기");
  homeBtn.onclick = () => renderSplash();
  list.appendChild(homeBtn);
  
  view.appendChild(list);
  appContainer.appendChild(view);
};

// Start App
renderSplash();
