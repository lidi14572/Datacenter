const taskList = document.getElementById("task-list");
const taskCount = document.getElementById("task-count");
const priorityCount = document.getElementById("priority-count");
const refreshButton = document.getElementById("refresh");
const lookupResult = document.getElementById("lookup-result");

const renderTasks = (tasks) => {
  taskCount.textContent = tasks.length;
  priorityCount.textContent = tasks.filter((task) => task.priority === 1).length;
  taskList.innerHTML = "";

  if (tasks.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "今日暂无维修任务。";
    taskList.appendChild(empty);
    return;
  }

  tasks.forEach((task) => {
    const row = document.createElement("div");
    row.className = "table-row";
    row.innerHTML = `
      <span>#${task.id}</span>
      <span>${task.room}</span>
      <span>${task.device}</span>
      <span>${task.serial_number}</span>
      <span>P${task.priority}</span>
      <span>${task.engineer}</span>
      <span>${task.status}</span>
    `;
    taskList.appendChild(row);
  });
};

const loadTasks = async () => {
  const response = await fetch("/api/tasks/today");
  const data = await response.json();
  renderTasks(data.tasks || []);
};

const renderLookup = (serial, device) => {
  lookupResult.innerHTML = "";
  const wrapper = document.createElement("div");
  wrapper.className = "lookup-result";
  if (!device) {
    wrapper.innerHTML = `<strong>未找到序列号：${serial}</strong>`;
    lookupResult.appendChild(wrapper);
    return;
  }

  wrapper.innerHTML = `
    <h3>设备：${device.device}</h3>
    <div class="lookup-grid">
      <div class="lookup-item"><strong>序列号</strong><br />${device.serial_number}</div>
      <div class="lookup-item"><strong>机房</strong><br />${device.room}</div>
      <div class="lookup-item"><strong>机柜</strong><br />${device.cabinet}</div>
      <div class="lookup-item"><strong>U 位</strong><br />${device.u_position}</div>
      <div class="lookup-item"><strong>归属</strong><br />${device.owner || "-"}</div>
    </div>
  `;
  lookupResult.appendChild(wrapper);
};

const submitLookup = async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  const serial = formData.get("serial").trim();
  if (!serial) {
    return;
  }
  const response = await fetch(`/api/devices/lookup?serial=${encodeURIComponent(serial)}`);
  const data = await response.json();
  renderLookup(serial, data.device);
};

refreshButton.addEventListener("click", loadTasks);

const lookupForm = document.getElementById("lookup-form");
lookupForm.addEventListener("submit", submitLookup);

loadTasks();
