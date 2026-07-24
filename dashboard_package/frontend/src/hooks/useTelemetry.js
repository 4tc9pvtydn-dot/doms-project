import { useEffect, useRef, useState } from "react";
import { REDLINE } from "@/lib/dashUtils";

// Gear speed bands in mph
const GEARS = [
  { g: 1, lo: 0, hi: 9 },
  { g: 2, lo: 9, hi: 21 },
  { g: 3, lo: 21, hi: 39 },
  { g: 4, lo: 39, hi: 59 },
  { g: 5, lo: 59, hi: 92 },
];

function gearForSpeed(mph) {
  if (mph < 1.2) return 0; // Neutral / idle
  for (const gg of GEARS) if (mph >= gg.lo && mph < gg.hi) return gg.g;
  return 5;
}

const initial = {
  speed: 0,
  rpm: 1050,
  gear: 0,
  throttle: 0,
  fuel: 64,
  cht: 78,
  afr: 13.2,
  volt: 12.6,
  satellites: 9,
  odometer: 1245,
  tripA: 0,
  tripB: 0,
  rideTime: 0,
  engineRuntime: 0,
  avgSpeed: 0,
  maxSpeed: 0,
  peakRpm: 1050,
  peakTemp: 78,
  bestSpeed: 0,
  fanOn: false,
  accel0_30: null,
  accel0_60: null,
  quarter: null,
  running: true,
};

export default function useTelemetry(running, override) {
  const [data, setData] = useState(initial);
  const s = useRef({
    ...initial,
    targetSpeed: 0,
    changeIn: 0,
    launchDist: 0,
    launchTime: 0,
    launching: false,
    distance: 0,
  });

  const overrideRef = useRef(override);
  overrideRef.current = override;

  useEffect(() => {
    if (!running) return;
    const dt = 0.1; // seconds per tick
    const id = setInterval(() => {
      const st = s.current;
      const ov = overrideRef.current;

      // ---- speed target wander ----
      st.changeIn -= dt;
      if (st.changeIn <= 0) {
        st.changeIn = 2 + Math.random() * 4;
        const r = Math.random();
        if (r < 0.15) st.targetSpeed = 0; // stop
        else if (r < 0.35) st.targetSpeed = 20 + Math.random() * 20;
        else st.targetSpeed = 35 + Math.random() * 48;
      }

      // ease speed toward target
      const accelRate = st.targetSpeed > st.speed ? 9 : 14;
      const diff = st.targetSpeed - st.speed;
      st.throttle = Math.max(0, Math.min(1, diff / 30 + 0.15));
      st.speed += Math.sign(diff) * Math.min(Math.abs(diff), accelRate * dt);
      if (st.speed < 0.05) st.speed = 0;

      // manual override for speed
      if (ov && ov.speed != null) st.speed = ov.speed;

      // ---- gear + rpm ----
      const gear = gearForSpeed(st.speed);
      let rpm;
      if (gear === 0) {
        rpm = 1000 + Math.random() * 120;
      } else {
        const band = GEARS[gear - 1];
        const frac = (st.speed - band.lo) / (band.hi - band.lo);
        rpm = 2400 + frac * 5400 + (Math.random() * 240 - 120);
        rpm += st.throttle * 350;
      }
      rpm = Math.max(900, Math.min(REDLINE + 100, rpm));
      if (ov && ov.rpm != null) rpm = ov.rpm;
      st.rpm = rpm;
      st.gear = gear;

      // ---- distance / trips / odo ----
      const miThisTick = (st.speed * dt) / 3600;
      st.distance += miThisTick;
      st.odometer += miThisTick;
      st.tripA += miThisTick;
      st.tripB += miThisTick;
      st.rideTime += dt;
      if (st.speed > 1 || gear > 0) st.engineRuntime += dt;

      // ---- CHT (heat builds with rpm, sheds when low) ----
      const targetT = 70 + (rpm / REDLINE) * 135 + st.throttle * 15;
      st.cht += (targetT - st.cht) * 0.02;
      if (ov && ov.cht != null) st.cht = ov.cht;

      // ---- AFR ----
      let afrTarget = 13.2;
      if (st.throttle > 0.55) afrTarget = 12.4; // rich under load
      else if (diff < -2) afrTarget = 14.2; // lean on decel
      st.afr += (afrTarget - st.afr) * 0.12 + (Math.random() * 0.1 - 0.05);
      if (ov && ov.afr != null) st.afr = ov.afr;

      // ---- Voltage ----
      const vTarget = rpm > 1500 ? 14.1 : 12.5;
      st.volt += (vTarget - st.volt) * 0.05 + (Math.random() * 0.04 - 0.02);
      if (ov && ov.volt != null) st.volt = ov.volt;

      // ---- Fuel slow drain ----
      if (ov && ov.fuel != null) st.fuel = ov.fuel;
      else st.fuel = Math.max(0, st.fuel - miThisTick * 0.9);

      // ---- Satellites wander ----
      if (Math.random() < 0.03)
        st.satellites = Math.max(4, Math.min(12, st.satellites + (Math.random() < 0.5 ? -1 : 1)));

      // ---- Fan ----
      st.fanOn = st.cht > 170;

      // ---- peaks + averages ----
      st.maxSpeed = Math.max(st.maxSpeed, st.speed);
      st.bestSpeed = st.maxSpeed;
      st.peakRpm = Math.max(st.peakRpm, rpm);
      st.peakTemp = Math.max(st.peakTemp, st.cht);
      st.avgSpeed = st.rideTime > 0 ? (st.distance / (st.rideTime / 3600)) : 0;

      // ---- 0-30 / 0-60 / quarter (launch detection) ----
      if (st.speed < 0.6) {
        st.launching = true;
        st.launchTime = 0;
        st.launchDist = 0;
      } else if (st.launching) {
        st.launchTime += dt;
        st.launchDist += miThisTick;
        if (st.speed >= 30 && st.accel0_30 == null) st.accel0_30 = st.launchTime;
        if (st.speed >= 60 && st.accel0_60 == null) st.accel0_60 = st.launchTime;
        if (st.launchDist >= 0.25 && st.quarter == null) st.quarter = st.launchTime;
      }

      setData({
        speed: st.speed,
        rpm: st.rpm,
        gear: st.gear,
        throttle: st.throttle,
        fuel: st.fuel,
        cht: st.cht,
        afr: st.afr,
        volt: st.volt,
        satellites: st.satellites,
        odometer: st.odometer,
        tripA: st.tripA,
        tripB: st.tripB,
        rideTime: st.rideTime,
        engineRuntime: st.engineRuntime,
        avgSpeed: st.avgSpeed,
        maxSpeed: st.maxSpeed,
        peakRpm: st.peakRpm,
        peakTemp: st.peakTemp,
        bestSpeed: st.bestSpeed,
        fanOn: st.fanOn,
        accel0_30: st.accel0_30,
        accel0_60: st.accel0_60,
        quarter: st.quarter,
        running: true,
      });
    }, 100);
    return () => clearInterval(id);
  }, [running]);

  const resetTrip = (which) => {
    if (which === "A") s.current.tripA = 0;
    if (which === "B") s.current.tripB = 0;
    if (which === "perf") {
      s.current.accel0_30 = null;
      s.current.accel0_60 = null;
      s.current.quarter = null;
      s.current.peakRpm = s.current.rpm;
      s.current.peakTemp = s.current.cht;
      s.current.maxSpeed = 0;
      s.current.bestSpeed = 0;
    }
  };

  return { data, resetTrip };
}
