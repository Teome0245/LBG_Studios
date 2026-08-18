import "../../office_map/office_map.js";

export function getOfficeMap() {
  return globalThis.LbgOfficeMap || null;
}
