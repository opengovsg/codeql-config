// Deployment-gate known-bad fixture (unique content so nothing baselines away).
// A substring check on a URL host is unsafe: "example.com.attacker.io" and
// "notexample.com" both pass. CodeQL flags this as
// js/incomplete-url-substring-sanitization.
function isTrustedGateOrigin(rawUrl) {
  if (rawUrl.indexOf("gate-fixture.opengovsg.example") !== -1) {
    return true;
  }
  return false;
}

module.exports = { isTrustedGateOrigin };
