const fs = require("fs");
const { JSDOM } = require("../demo-studio/node_modules/jsdom");
const html = fs.readFileSync(
  "plugins/robot_windows/lockbox_window/lockbox_window.html",
  "utf8",
);
const dom = new JSDOM(html, {
  runScripts: "dangerously",
  url: "http://localhost/",
});
const w = dom.window,
  d = w.document,
  messages = [];
w.robotWindow = { send: (m) => messages.push(JSON.parse(m)) };
const s = JSON.parse(
  fs.readFileSync("results/webots_smoke.json", "utf8"),
).final_status;
w.renderStatus(s);
const checks = {};
checks.secured_headline =
  d.getElementById("headline").textContent === "Empty. Box secured.";
checks.twenty_five_sensor_cells = d.querySelectorAll(".sensor").length === 25;
checks.event_history_visible =
  d.querySelectorAll("#events li").length === s.events.length;
d.getElementById("role").value = "owner";
d.getElementById("code").value = "1357";
d.getElementById("access-form").dispatchEvent(
  new w.Event("submit", { bubbles: true, cancelable: true }),
);
checks.access_role_and_fresh_id =
  messages[0].role === "owner" &&
  messages[0].code === "1357" &&
  !!messages[0].request_id;
checks.code_cleared_after_submit = d.getElementById("code").value === "";
d.querySelector('[data-action="jam_latch"]').click();
checks.lab_action_forwarded = messages[1].action === "jam_latch";
w.renderStatus({
  ...s,
  phase: "FAULT",
  secured: false,
  fault: true,
  latch: "moving",
});
checks.fault_cannot_display_secured =
  d.getElementById("hero").classList.contains("state-fault") &&
  d.getElementById("headline").textContent === "Bolt position fault.";
w.renderStatus({ ...s, link: "offline", pending: 4 });
checks.offline_queue_displayed =
  d.getElementById("queue").textContent === "4 PENDING";
w.renderStatus({
  ...s,
  phase: "FAULT",
  secured: false,
  fault: true,
  fault_reason: "sensor",
  latch_position_m: null,
  door_angle_rad: null,
  parcel_distances_m: Array(25).fill(null),
});
checks.sensor_fault_explained =
  d.getElementById("headline").textContent === "Sensor feedback unavailable.";
checks.missing_values_rendered =
  d.getElementById("bolt").textContent === "unavailable" &&
  d.querySelector(".sensor").textContent === "N/A";
w.renderStatus({
  ...s,
  phase: "FAULT",
  secured: false,
  fault: true,
  fault_reason: "door",
});
checks.door_fault_explained =
  d.getElementById("headline").textContent === "Door closing fault.";
checks.door_fixture_available =
  !!d.querySelector('[data-action="jam_door"]') &&
  !!d.querySelector('[data-action="release_door"]');
w.renderStatus({
  ...s,
  secured: false,
  phase: "ACCESS",
  delivery_pending: true,
});
checks.pending_delivery_explained = d
  .getElementById("summary")
  .textContent.includes("Delivery will be confirmed");
w.renderStatus({
  ...s,
  owner_code_used: true,
  grant: "none",
  last_access_result: true,
});
checks.used_owner_code_explained = d
  .getElementById("access-result")
  .textContent.includes("Owner code used");
const result = {
  passed: Object.values(checks).every(Boolean),
  method:
    "DOM integration with recorded Webots status and injected fault states",
  checks,
};
fs.writeFileSync(
  "results/dashboard_validation.json",
  JSON.stringify(result, null, 2),
);
console.log(JSON.stringify(result));
if (!result.passed) process.exitCode = 1;
