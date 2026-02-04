const permissionList = document.getElementById("permission-list");
const orderInfo = document.getElementById("order-info");
const deviceList = document.getElementById("device-list");
const deviceCount = document.getElementById("device-count");
const templateTime = document.getElementById("template-time");

const toListItem = (item) => {
  const wrapper = document.createElement("div");
  wrapper.className = "list-item";
  wrapper.innerHTML = `<strong>${item.role}</strong>${item.permissions.join(" · ")}`;
  return wrapper;
};

const renderDevices = (devices) => {
  deviceList.innerHTML = "";
  deviceCount.textContent = devices.length;
  templateTime.textContent = new Date().toLocaleString("zh-CN");

  if (devices.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "暂无设备台账，请上传模板。";
    deviceList.appendChild(empty);
    return;
  }

  devices.forEach((device) => {
    const row = document.createElement("div");
    row.className = "table-row device";
    row.innerHTML = `
      <span>${device.serial_number}</span>
      <span>${device.device}</span>
      <span>${device.room}</span>
      <span>${device.cabinet}</span>
      <span>${device.u_position}</span>
      <span>${device.owner || "-"}</span>
    `;
    deviceList.appendChild(row);
  });
};

const loadPermissions = async () => {
  const response = await fetch("/api/permissions");
  const data = await response.json();
  permissionList.innerHTML = "";
  data.forEach((item) => permissionList.appendChild(toListItem(item)));
};

const loadOrder = async () => {
  const response = await fetch("/api/repair-order");
  const data = await response.json();
  orderInfo.innerHTML = `
    <strong>${data.strategy}</strong>
    <div class="muted">${data.notes}</div>
  `;
};

const loadDevices = async () => {
  const response = await fetch("/api/devices");
  const data = await response.json();
  renderDevices(data.devices || []);
};

const submitPermission = async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  const role = formData.get("role");
  const permissions = formData
    .get("permissions")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  await fetch("/api/permissions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, permissions }),
  });

  event.target.reset();
  loadPermissions();
};

const submitOrder = async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  await fetch("/api/repair-order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      strategy: formData.get("strategy"),
      notes: formData.get("notes"),
    }),
  });

  event.target.reset();
  loadOrder();
};

const submitDeviceTemplate = async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  const file = formData.get("file");
  if (!file) {
    return;
  }
  const content = await file.text();
  const rows = content.trim().split(/\r?\n/);
  if (rows.length <= 1) {
    return;
  }
  const headers = rows[0].split(",").map((item) => item.trim());
  const devices = rows.slice(1).map((row) => {
    const values = row.split(",");
    return headers.reduce((acc, header, index) => {
      acc[header] = (values[index] || "").trim();
      return acc;
    }, {});
  });

  const response = await fetch("/api/devices/bulk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ devices }),
  });
  const data = await response.json();
  renderDevices(data.devices || []);
  event.target.reset();
};

const permissionForm = document.getElementById("permission-form");
const orderForm = document.getElementById("order-form");
const deviceForm = document.getElementById("device-form");

permissionForm.addEventListener("submit", submitPermission);
orderForm.addEventListener("submit", submitOrder);
deviceForm.addEventListener("submit", submitDeviceTemplate);

loadPermissions();
loadOrder();
loadDevices();
