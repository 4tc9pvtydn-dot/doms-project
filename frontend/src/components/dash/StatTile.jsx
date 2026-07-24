export default function StatTile({ label, value, unit, color = "t-white", flash, big, testId }) {
  return (
    <div className="panel flex flex-col justify-center px-4 py-2" data-testid={testId}>
      <div className="section-title mb-1">{label}</div>
      <div className="flex items-baseline gap-1">
        <span
          className={`digital font-bold tabnum leading-none ${color} ${flash ? "flash" : ""}`}
          style={{ fontSize: big ? 40 : 30 }}
        >
          {value}
        </span>
        {unit && <span className="text-[12px] t-dim font-semibold">{unit}</span>}
      </div>
    </div>
  );
}
