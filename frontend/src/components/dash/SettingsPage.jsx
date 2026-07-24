import { Sun, Ruler, Clock, Gauge, SlidersHorizontal, Power } from "lucide-react";

function Row({ icon, label, children, testId }) {
  return (
    <div className="panel flex items-center justify-between px-4 py-[10px]" data-testid={testId}>
      <div className="flex items-center gap-2 section-title text-[12px]">
        {icon}
        {label}
      </div>
      <div className="flex items-center gap-3">{children}</div>
    </div>
  );
}

export default function SettingsPage({ settings, setSettings, onShutdown }) {
  const set = (patch) => setSettings((s) => ({ ...s, ...patch }));
  return (
    <div className="carbon absolute inset-0 flex flex-col px-5 pt-3 pb-8 overflow-hidden" data-testid="settings-page">
      <div className="section-title text-[13px] mb-3">SETTINGS</div>
      <div className="flex flex-col gap-[10px] flex-1">
        <Row icon={<Sun size={14} />} label="Brightness" testId="setting-brightness">
          <input
            type="range"
            min="20"
            max="100"
            value={settings.brightness}
            onChange={(e) => set({ brightness: Number(e.target.value) })}
            className="w-[220px] accent-amber-400"
            data-testid="brightness-slider"
          />
          <span className="digital w-[42px] text-right t-white font-bold">{settings.brightness}%</span>
        </Row>

        <Row icon={<Ruler size={14} />} label="Units" testId="setting-units">
          {["mph", "kph"].map((u) => (
            <button
              key={u}
              onClick={() => set({ units: u })}
              className={`px-3 py-1 rounded-md text-[13px] font-bold tracking-wider ${settings.units === u ? "bg-amber-400 text-black" : "text-white/70 border border-white/15"}`}
              data-testid={`units-${u}`}
            >
              {u.toUpperCase()}
            </button>
          ))}
        </Row>

        <Row icon={<Clock size={14} />} label="Clock" testId="setting-clock">
          {["24h", "12h"].map((c) => (
            <button
              key={c}
              onClick={() => set({ clock24: c === "24h" })}
              className={`px-3 py-1 rounded-md text-[13px] font-bold tracking-wider ${(settings.clock24 ? "24h" : "12h") === c ? "bg-amber-400 text-black" : "text-white/70 border border-white/15"}`}
              data-testid={`clock-${c}`}
            >
              {c.toUpperCase()}
            </button>
          ))}
        </Row>

        <Row icon={<Gauge size={14} />} label="CHT Warn Limits (°C)" testId="setting-limits">
          <div className="flex items-center gap-2">
            <span className="text-[11px] t-amber">Amber</span>
            <input type="range" min="100" max="210" value={settings.limits.chtAmber}
              onChange={(e) => set({ limits: { ...settings.limits, chtAmber: Number(e.target.value) } })}
              className="w-[80px] accent-amber-400" data-testid="cht-amber-slider" />
            <span className="digital w-[34px] text-right t-amber">{settings.limits.chtAmber}</span>
            <span className="text-[11px] t-red ml-2">Red</span>
            <input type="range" min="130" max="240" value={settings.limits.chtRed}
              onChange={(e) => set({ limits: { ...settings.limits, chtRed: Number(e.target.value) } })}
              className="w-[80px] accent-red-500" data-testid="cht-red-slider" />
            <span className="digital w-[34px] text-right t-red">{settings.limits.chtRed}</span>
          </div>
        </Row>

        <Row icon={<SlidersHorizontal size={14} />} label="Sensor Calibration" testId="setting-calibration">
          <span className="text-[12px] t-dim">Fuel · RPM · CHT · AFR — auto</span>
        </Row>
      </div>

      <button
        onClick={onShutdown}
        className="flex items-center justify-center gap-2 py-[10px] rounded-lg bg-red-600/90 hover:bg-red-600 text-white font-bold tracking-widest text-[14px] active:scale-95 transition-transform mt-2"
        data-testid="shutdown-btn"
      >
        <Power size={16} /> SHUTDOWN
      </button>
    </div>
  );
}
