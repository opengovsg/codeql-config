// Deployment-gate known-bad fixture (unique content so nothing baselines away).
// A root CDN with no path in a Content-Security-Policy scriptSrc is flagged by
// javascript/no-root-cdn. This deliberately targets an OGP CUSTOM-pack rule,
// not a built-in one: the repo's own default CodeQL setup does not load the OGP
// packs, so it leaves this fixture alone, while the deployment gate (which loads
// the packs from codeql-config.yml) still detects it. That keeps the intentional
// vulnerability out of the repo's real code-scanning alerts.
function configureGateCsp(contentSecurityPolicy) {
  const rootCdn = "cdnjs.cloudflare.com";
  return contentSecurityPolicy({ scriptSrc: rootCdn });
}

module.exports = { configureGateCsp };
