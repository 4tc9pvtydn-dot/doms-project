import RpmBar from "@/components/dash/RpmBar";
import VerticalBar from "@/components/dash/VerticalBar";
import {
  fuelStatus,
  chtStatus,
  afrStatus,
  voltStatus,
  colorClass,
  toDisplaySpeed,
  toDisplayDist,
  speedUnit,
  distUnit,
} from "@/lib/dashUtils";
import { Fuel, Thermometer, Fan } from "lucide-react";
import { motion } from "framer-motion";

export default function RidePage({ data, settings, clock }) {
  const fuel = fuelStatus(data.fuel);
  const cht = chtStatus(data.cht, settings.limits);
  const afr = afrStatus(data.afr);
  const volt = voltStatus(data.volt, data.running);

  const spd = Math.round(toDisplaySpeed(data.speed, settings.units));
  const gearLabel = data.gear === 0 ? "N" : data.gear;

  return (
    <div className="carbon absolute inset-0 flex flex-col px-4 pt-2 pb-7" data-testid="ride-page">
      {/* Top bar */}
      <div className="flex items-center justify-between h-[26px]">
        <div className="digital text-[16px] font-extrabold tracking-widest whitespace-nowrap">
          <span className="t-white">DOMS</span> <span className="t-amber">RB252</span>
        </div>
        <div className="digital text-[16px] font-bold tabnum t-white text-right" data-testid="clock">
          {clock}
        </div>
      </div>

      {/* Middle */}
      <div className="flex-1 flex items-stretch gap-3 py-2">
        <VerticalBar value={data.fuel / 100} status={fuel} label="FUEL" icon={<Fuel size={11} />} testId="fuel-bar" />

        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="w-[300px] mb-2">
            <RpmBar rpm={data.rpm} testId="rpm-bar" heightClass="h-[34px]" />
          </div>
          <div className="flex items-baseline">
            <motion.div
              key="spd"
              className="digital font-black leading-none t-white tabnum"
              style={{ fontSize: 150, textShadow: "0 0 24px rgba(255,255,255,0.25)" }}
              data-testid="speed-value"
            >
              {spd}
            </motion.div>
          </div>
          <div className="section-title -mt-1 mb-1" data-testid="speed-unit">
            {speedUnit(settings.units)}
          </div>
          <div
            className="digital font-black leading-none t-amber tabnum"
            style={{ fontSize: 60, textShadow: "0 0 20px rgba(251,191,36,0.35)" }}
            data-testid="gear-value"
          >
            {gearLabel}
          </div>
          <div className="section-title">GEAR</div>
        </div>

        <VerticalBar value={(data.cht - 40) / 200} status={cht} label="TEMP" icon={<Thermometer size={11} />} testId="temp-bar" />
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-4 items-center h-[30px] text-center">
        <div className="text-left" data-testid="afr-value">
          <span className="section-title mr-1">AFR</span>
          <span className={`digital text-[22px] font-bold tabnum ${colorClass[afr.color]} ${afr.danger ? "flash" : ""}`}>
            {data.afr.toFixed(1)}
          </span>
        </div>
        <div className="flex items-center justify-center gap-1" data-testid="voltage-value">
          <span className={`digital text-[20px] font-bold tabnum ${colorClass[volt.color]}`}>
            {data.volt.toFixed(1)}V
          </span>
          {data.fanOn && <Fan size={14} className="t-green animate-spin" style={{ animationDuration: "1.4s" }} data-testid="fan-icon" />}
        </div>
        <div className="digital text-[16px] font-semibold tabnum t-dim" data-testid="odometer">
          {Math.floor(toDisplayDist(data.odometer, settings.units)).toLocaleString()} {distUnit(settings.units).toLowerCase()}
        </div>
        <div />
      </div>
    </div>
  );
}
