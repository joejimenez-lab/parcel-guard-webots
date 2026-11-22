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
w.renderStatus({ ...s, storage: "saved", recovery_count: 2 });
checks.saved_state_visible = d.getElementById("storage").textContent === "Saved locally" &&
  d.getElementById("recoveries").textContent === "2";
checks.restart_enabled_for_saved_state = !d.querySelector('[data-action="restart_controller"]').disabled;
d.querySelector('[data-action="severe_impact"]').click();
checks.strong_impact_requests_physical_fixture = messages.at(-1).action === "impact" && messages.at(-1).severe === true;
w.renderStatus({ ...s, storage: "memory" });
checks.restart_disabled_without_saved_state = d.querySelector('[data-action="restart_controller"]').disabled;
w.renderStatus({ ...s, secured: false, fault: true, fault_reason: "storage", storage: "fault" });
checks.storage_fault_explained = d.getElementById("headline").textContent === "Saved state unavailable.";
checks.sensor_fault_fixtures_available = !!d.querySelector('[data-action="sensor_fault"]') &&
  !!d.querySelector('[data-action="sensor_restore"]');
const protectedStatus = {...s, security:{enabled:true,lockdown:false,incident:"",credentials:[]}};
w.renderStatus(protectedStatus);
checks.owner_console_visible_in_security_mode = !d.getElementById("owner-security").hidden;
checks.code_issuance_requires_owner_session = d.getElementById("issue-code").disabled;
d.getElementById("owner-password").value="example-password";
d.getElementById("owner-login-form").dispatchEvent(new w.Event("submit",{bubbles:true,cancelable:true}));
checks.password_only_owner_sign_in = messages.at(-1).action==="owner_login" && messages.at(-1).password==="example-password" && !("otp" in messages.at(-1));
checks.no_authenticator_field = !d.getElementById("owner-otp");
checks.owner_secrets_cleared_after_submit = !d.getElementById("owner-password").value;
w.receiveMessage({type:"security_reply",action:"owner_login",ok:true,token:"test-owner-token",expires:s.time+300,session:s.session,message:"Owner verified."});
checks.verified_owner_can_issue_code = !d.getElementById("issue-code").disabled;
d.getElementById("issue-code-form").dispatchEvent(new w.Event("submit",{bubbles:true,cancelable:true}));
checks.issuance_sends_session_scope_and_lifetime = messages.at(-1).action==="issue_code" && messages.at(-1).token==="test-owner-token" && messages.at(-1).role==="courier" && messages.at(-1).ttl_s===300;
w.receiveMessage({type:"security_reply",action:"issue_code",ok:true,id:"code-a",code:"82468135",role:"courier",expires:s.time+300,session:s.session,message:"Code created."});
checks.private_code_visible_before_next_status = d.getElementById("issued-code").textContent==="82468135";
const credential={id:"code-a",role:"courier",expires:s.time+300,used:false,revoked:false};
w.renderStatus({...protectedStatus,security:{...protectedStatus.security,credentials:[credential]}});
d.querySelector("#credentials button").click();
checks.revocation_targets_credential_id = messages.at(-1).action==="revoke_code" && messages.at(-1).credential_id==="code-a";
w.renderStatus({...protectedStatus,security:{...protectedStatus.security,credentials:[{...credential,used:true}]}});
checks.used_code_removed_from_private_display = d.getElementById("issued-code").textContent==="";
const lockedStatus={...protectedStatus,phase:"LOCKDOWN",all_events:[...(s.all_events||[]),{id:100000,kind:"tamper"}],security:{...protectedStatus.security,lockdown:true,incident:"impact detected"}};
w.renderStatus(lockedStatus);
checks.lockdown_prominent_and_previous_owner_session_cancelled = d.getElementById("headline").textContent.includes("Security lockdown") && d.getElementById("issue-code").disabled && d.getElementById("clear-lockdown").disabled;
w.receiveMessage({type:"security_reply",action:"owner_login",ok:true,token:"fresh-owner-token",expires:s.time+300,session:s.session,message:"Owner verified again."});
checks.fresh_owner_can_clear_physically_secure_lockdown = !d.getElementById("clear-lockdown").disabled;
w.renderStatus({...lockedStatus,secured:false});
checks.lockdown_clear_waits_for_physical_security = d.getElementById("clear-lockdown").disabled;
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
