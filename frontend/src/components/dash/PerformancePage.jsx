import StatTile from "@/components/dash/StatTile";
import { toDisplaySpeed, speedUnit } from "@/lib/dashUtils";

export default function PerformancePage({ data, settings, onResetTrip }) {
  const su = speedUnit(settings.units);
  const t = (v) => (v == null ? "—" : `${v.toFixed(2)}`);
  return (
    <div className="carbon absolute inset-0 flex flex-col px-5 pt-3 pb-8" data-testid="performance-page">
      <div className="section-title text-[13px] mb-3">PERFORMANCE</div>
      <div className="grid grid-cols-3 gap-3 flex-1 content-center">
        <StatTile label="0-30" value={t(data.accel0_30)} unit="s" color="t-green" big testId="perf-030" />
        <StatTile label="0-60" value={t(data.accel0_60)} unit="s" color="t-green" big testId="perf-060" />
        <StatTile label="1/4 Mile" value={t(data.quarter)} unit="s" color="t-amber" big testId="perf-quarter" />
        <StatTile label="Peak RPM" value={Math.round(data.peakRpm).toLocaleString()} color="t-red" testId="perf-peakrpm" />
        <StatTile label="Peak Temp" value={`${Math.round(data.peakTemp)}°`} color="t-red" testId="perf-peaktemp" />
        <StatTile label="Best Speed" value={Math.round(toDisplaySpeed(data.bestSpeed, settings.units))} unit={su} color="t-amber" testId="perf-bestspeed" />
      </div>
      <button
        className="panel py-2 mt-3 text-[13px] font-bold tracking-widest active:scale-95 transition-transform"
        onClick={() => onResetTrip("perf")}
        data-testid="reset-perf-btn"
      >
        RESET PERFORMANCE STATS
      </button>
    </div>
  );
}
