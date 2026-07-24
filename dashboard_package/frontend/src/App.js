import { useEffect, useRef, useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import "@/App.css";
import useTelemetry from "@/hooks/useTelemetry";
import StartupScreen from "@/components/dash/StartupScreen";
import RidePage from "@/components/dash/RidePage";
import EnginePage from "@/components/dash/EnginePage";
import GpsPage from "@/components/dash/GpsPage";
import PerformancePage from "@/components/dash/PerformancePage";
import SettingsPage from "@/components/dash/SettingsPage";
import PageIndicator from "@/components/dash/PageIndicator";
import WarningBanner from "@/components/dash/WarningBanner";
import { chtStatus, afrStatus } from "@/lib/dashUtils";
import { Power } from "lucide-react";

const PAGE_COUNT = 5;

function useClock(clock24) {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  let h = now.getHours();
  const m = String(now.getMinutes()).padStart(2, "0");
  if (!clock24) {
    h = h % 12 || 12;
    return `${h}:${m}`;
  }
  return `${String(h).padStart(2, "0")}:${m}`;
}

function useFitScale() {
  const [scale, setScale] = useState(1);
  useEffect(() => {
    const fit = () => {
      const s = Math.min(window.innerWidth / 640, window.innerHeight / 480);
      setScale(s);
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);
  return scale;
}

export default function App() {
  const [booted, setBooted] = useState(false);
  const [shutdown, setShutdown] = useState(false);
  const [page, setPage] = useState(0);
  const [dir, setDir] = useState(1);
  const [settings, setSettings] = useState({
    brightness: 100,
    units: "mph",
    clock24: true,
    limits: { chtAmber: 195, chtRed: 215 },
  });

  const { data, resetTrip } = useTelemetry(booted && !shutdown, null);
  const clock = useClock(settings.clock24);
  const scale = useFitScale();

  useEffect(() => {
    const t = setTimeout(() => setBooted(true), 2600);
    return () => clearTimeout(t);
  }, []);

  const goto = useCallback((next) => {
    setPage((p) => {
      const clamped = Math.max(0, Math.min(PAGE_COUNT - 1, next));
      setDir(clamped > p ? 1 : -1);
      return clamped;
    });
  }, []);

  // keyboard for desktop demo
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "ArrowRight") goto(page + 1);
      if (e.key === "ArrowLeft") goto(page - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [page, goto]);

  // swipe
  const startX = useRef(null);
  const onPointerDown = (e) => (startX.current = e.clientX);
  const onPointerUp = (e) => {
    if (startX.current == null) return;
    const dx = e.clientX - startX.current;
    if (dx < -50) goto(page + 1);
    else if (dx > 50) goto(page - 1);
    startX.current = null;
  };

  // warnings
  const cht = chtStatus(data.cht, settings.limits);
  const afr = afrStatus(data.afr);
  let warning = null;
  if (cht.danger) warning = "CYLINDER TEMP CRITICAL";
  else if (afr.danger) warning = "AFR DANGER — CHECK MIXTURE";

  const pages = [
    <RidePage key="ride" data={data} settings={settings} clock={clock} />,
    <EnginePage key="engine" data={data} settings={settings} />,
    <GpsPage key="gps" data={data} settings={settings} onResetTrip={resetTrip} />,
    <PerformancePage key="perf" data={data} settings={settings} onResetTrip={resetTrip} />,
    <SettingsPage key="settings" settings={settings} setSettings={setSettings} onShutdown={() => setShutdown(true)} />,
  ];

  const brightness = 0.35 + (settings.brightness / 100) * 0.65;

  return (
    <div className="dash-viewport">
      <div
        className="dash-frame carbon"
        style={{ transform: `scale(${scale})`, filter: `brightness(${brightness})` }}
        data-testid="dash-frame"
      >
        {/* Boot */}
        <AnimatePresence>
          {!booted && (
            <motion.div key="boot" exit={{ opacity: 0 }} transition={{ duration: 0.5 }} className="absolute inset-0 z-[70]">
              <StartupScreen />
            </motion.div>
          )}
        </AnimatePresence>

        {booted && !shutdown && (
          <div
            className="absolute inset-0 touch-none"
            onPointerDown={onPointerDown}
            onPointerUp={onPointerUp}
            data-testid="swipe-area"
          >
            <WarningBanner message={warning} />
            <AnimatePresence custom={dir} mode="popLayout">
              <motion.div
                key={page}
                custom={dir}
                initial={{ x: dir * 640, opacity: 0.4 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -dir * 640, opacity: 0.4 }}
                transition={{ type: "spring", stiffness: 260, damping: 30 }}
                className="absolute inset-0"
              >
                {pages[page]}
              </motion.div>
            </AnimatePresence>

            {/* Global page indicator */}
            <div className="absolute bottom-[6px] left-0 right-0 flex justify-center z-40 pointer-events-none">
              <PageIndicator count={PAGE_COUNT} index={page} />
            </div>
          </div>
        )}

        {/* Shutdown overlay */}
        <AnimatePresence>
          {shutdown && (
            <motion.div
              key="shutdown"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute inset-0 z-[80] bg-black flex flex-col items-center justify-center gap-4"
              data-testid="shutdown-overlay"
            >
              <Power size={40} className="t-dim" />
              <div className="section-title text-[13px]">SYSTEM HALTED</div>
              <button
                onClick={() => { setShutdown(false); setBooted(false); setTimeout(() => setBooted(true), 2600); setPage(0); }}
                className="mt-2 px-5 py-2 rounded-lg border border-white/20 text-[13px] font-bold tracking-widest active:scale-95 transition-transform"
                data-testid="restart-btn"
              >
                RESTART
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
