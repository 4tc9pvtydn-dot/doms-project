import StatTile from "@/components/dash/StatTile";
import {
  toDisplaySpeed,
  toDisplayDist,
  speedUnit,
  distUnit,
  fmtTime,
} from "@/lib/dashUtils";
import { Satellite } from "lucide-react";

export default function GpsPage({ data, settings, onResetTrip }) {
  const su = speedUnit(settings.units);
  const du = distUnit(settings.units);
  const ds = (mph) => Math.round(toDisplaySpeed(mph, settings.units));
  const dd = (mi) => toDisplayDist(mi, settings.units).toFixed(1);

  return (
    <div className="carbon absolute inset-0 flex flex-col px-5 pt-3 pb-8" data-testid="gps-page">
      <div className="flex items-center justify-between mb-3">
        <div className="section-title text-[13px]">GPS</div>
        <div className="flex items-center gap-2 t-green" data-testid="gps-sats">
          <Satellite size={16} />
          <span className="digital text-[16px] font-bold tabnum">{data.satellites} SAT</span>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 flex-1 content-center">
        <StatTile label="Current" value={ds(data.speed)} unit={su} big testId="gps-current" />
        <StatTile label="Average" value={ds(data.avgSpeed)} unit={su} testId="gps-avg" />
        <StatTile label="Maximum" value={ds(data.maxSpeed)} unit={su} color="t-amber" testId="gps-max" />
        <StatTile label="Trip A" value={dd(data.tripA)} unit={du} testId="gps-tripa" />
        <StatTile label="Trip B" value={dd(data.tripB)} unit={du} testId="gps-tripb" />
        <StatTile label="Ride Time" value={fmtTime(data.rideTime)} testId="gps-ridetime" />
      </div>
      <div className="flex gap-3 mt-3">
        <button
          className="panel flex-1 py-2 text-[13px] font-bold tracking-widest active:scale-95 transition-transform"
          onClick={() => onResetTrip("A")}
          data-testid="reset-tripa-btn"
        >
          RESET TRIP A
        </button>
        <button
          className="panel flex-1 py-2 text-[13px] font-bold tracking-widest active:scale-95 transition-transform"
          onClick={() => onResetTrip("B")}
          data-testid="reset-tripb-btn"
        >
          RESET TRIP B
        </button>
      </div>
    </div>
  );
}
