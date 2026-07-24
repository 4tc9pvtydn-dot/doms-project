import StatTile from "@/components/dash/StatTile";
import {
  afrStatus,
  chtStatus,
  voltStatus,
  colorClass,
  fmtTime,
} from "@/lib/dashUtils";
import { Fan } from "lucide-react";

export default function EnginePage({ data, settings }) {
  const afr = afrStatus(data.afr);
  const cht = chtStatus(data.cht, settings.limits);
  const volt = voltStatus(data.volt, data.running);

  return (
    <div className="carbon absolute inset-0 flex flex-col px-5 pt-3 pb-8" data-testid="engine-page">
      <div className="section-title text-[13px] mb-3">ENGINE</div>
      <div className="grid grid-cols-3 gap-3 flex-1 content-center">
        <StatTile label="RPM" value={Math.round(data.rpm).toLocaleString()} big testId="engine-rpm" />
        <StatTile label="AFR" value={data.afr.toFixed(1)} color={colorClass[afr.color]} flash={afr.danger} big testId="engine-afr" />
        <StatTile label="CHT" value={Math.round(data.cht)} unit="°C" color={colorClass[cht.color]} flash={cht.danger} big testId="engine-cht" />
        <StatTile label="EGT (future)" value="—" color="t-dim" testId="engine-egt" />
        <StatTile label="Battery" value={data.volt.toFixed(1)} unit="V" color={colorClass[volt.color]} big testId="engine-batt" />
        <div className="panel flex flex-col justify-center px-4 py-2" data-testid="engine-fan">
          <div className="section-title mb-1">Fan Status</div>
          <div className="flex items-center gap-2">
            <Fan size={22} className={data.fanOn ? "t-green animate-spin" : "t-dim"} style={{ animationDuration: "1.4s" }} />
            <span className={`digital text-[24px] font-bold ${data.fanOn ? "t-green" : "t-dim"}`}>
              {data.fanOn ? "ON" : "OFF"}
            </span>
          </div>
        </div>
      </div>
      <div className="panel px-4 py-2 mt-3" data-testid="engine-runtime">
        <span className="section-title mr-3">Engine Runtime</span>
        <span className="digital text-[22px] font-bold tabnum">{fmtTime(data.engineRuntime)}</span>
      </div>
    </div>
  );
}
