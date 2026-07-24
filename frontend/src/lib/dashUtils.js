// Color threshold helpers for the dashboard. Returns one of: green | amber | red
// plus a `danger` flag used for flashing.

export const REDLINE = 8500;
export const SHIFT_RPM = 7800;

export function fuelStatus(pct) {
  if (pct <= 12) return { color: "red", danger: true };
  if (pct <= 25) return { color: "amber", danger: false };
  return { color: "green", danger: false };
}

// CHT in °C
export function chtStatus(t, limits) {
  const amber = limits?.chtAmber ?? 195;
  const red = limits?.chtRed ?? 215;
  if (t >= red + 8) return { color: "red", danger: true };
  if (t >= red) return { color: "red", danger: false };
  if (t >= amber) return { color: "amber", danger: false };
  return { color: "green", danger: false };
}

// AFR: ideal ~12.8-13.4
export function afrStatus(afr) {
  if (afr < 11.4 || afr > 14.8) return { color: "red", danger: true };
  if (afr < 12.5 || afr > 13.8) return { color: "amber", danger: false };
  return { color: "green", danger: false };
}

// Voltage: charging good 13.2-14.8
export function voltStatus(v, running) {
  if (v > 15.2 || (running && v < 11.5)) return { color: "red", danger: true };
  if (v < 12.2) return { color: "amber", danger: false };
  if (running && v >= 13.2) return { color: "green", danger: false };
  return { color: "amber", danger: false };
}

export const colorClass = {
  green: "t-green",
  amber: "t-amber",
  red: "t-red",
};

export const fillClass = {
  green: "c-green",
  amber: "c-amber",
  red: "c-red",
};

export function fmtTime(totalSec) {
  const s = Math.max(0, Math.floor(totalSec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0)
    return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  return `${m}:${String(sec).padStart(2, "0")}`;
}

export function toDisplaySpeed(mph, units) {
  return units === "kph" ? mph * 1.60934 : mph;
}
export function toDisplayDist(mi, units) {
  return units === "kph" ? mi * 1.60934 : mi;
}
export function speedUnit(units) {
  return units === "kph" ? "KM/H" : "MPH";
}
export function distUnit(units) {
  return units === "kph" ? "KM" : "MI";
}
