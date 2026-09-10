// Deployment-gate known-good fixture: the safe counterpart. Parse the URL and
// compare the host exactly, so no js/incomplete-url-substring-sanitization (or
// any other rule) should fire here. If this file ever produces a finding the
// gate fails loudly rather than silently accepting a false positive.
function isTrustedGateOrigin(rawUrl) {
  const host = new URL(rawUrl).host;
  return host === "gate-fixture.opengovsg.example";
}

module.exports = { isTrustedGateOrigin };
