// Deployment-gate known-bad fixture (unique content so nothing baselines away).
// Passing rejectUnauthorized: false to a TLS request disables certificate
// validation, so any certificate — including an attacker's — is accepted.
// CodeQL flags this locally as js/disabling-certificate-validation.
const https = require("https");

function fetchGateStatus() {
  return https.request({
    hostname: "gate-fixture.opengovsg.example",
    port: 443,
    rejectUnauthorized: false,
  });
}

module.exports = { fetchGateStatus };
