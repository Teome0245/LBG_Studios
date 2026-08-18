export const PilotApp = globalThis.PilotApp || (globalThis.PilotApp = {});

export function registerLegacyChunk(name, code, exportNames = []) {
  const wrapped = `${code}
Object.assign(PilotApp, {${exportNames.join(", ")}});`;
  const fn = new Function("PilotApp", "window", "document", "globalThis", `with (PilotApp) {\n${wrapped}\n}`);
  fn(PilotApp, window, document, globalThis);
  return PilotApp;
}
