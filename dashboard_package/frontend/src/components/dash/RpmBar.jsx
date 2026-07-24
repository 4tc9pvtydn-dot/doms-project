import { REDLINE, SHIFT_RPM } from "@/lib/dashUtils";

// Center-out LED style RPM bar. Segments light from the middle outward.
export default function RpmBar({ rpm, testId, heightClass = "h-[22px]" }) {
  const perSide = 22;
  const frac = Math.max(0, Math.min(1, rpm / REDLINE));
  const litPerSide = Math.round(frac * perSide);
  const shift = rpm >= SHIFT_RPM;

  const segColor = (idx) => {
    // idx: 0 (center) .. perSide-1 (edge)
    const level = idx / perSide;
    if (level >= 0.82) return "lit-red";
    if (level >= 0.6) return "lit-amber";
    return "lit-white";
  };

  const left = [];
  const right = [];
  for (let i = 0; i < perSide; i++) {
    const lit = i < litPerSide;
    // left side edge is far-left => reverse so center fills first
    const leftIdx = perSide - 1 - i;
    left.push(
      <div
        key={`l${i}`}
        className={`rpm-seg ${leftIdx < litPerSide ? segColor(leftIdx) : ""}`}
      />
    );
    right.push(
      <div key={`r${i}`} className={`rpm-seg ${lit ? segColor(i) : ""}`} />
    );
  }

  return (
    <div
      data-testid={testId}
      className={`flex items-center gap-[2px] w-full ${heightClass} ${shift ? "shift-flash" : ""}`}
    >
      {left}
      <div className="w-[3px]" />
      {right}
    </div>
  );
}
