import { motion } from "framer-motion";
import { fillClass } from "@/lib/dashUtils";

// Vertical fill bar (fuel / temp). value is 0..1
export default function VerticalBar({ value, status, label, icon, testId }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const flash = status.danger ? "flash" : "";
  return (
    <div className="flex flex-col items-center h-full" data-testid={testId}>
      <div className="section-title mb-1 flex items-center gap-1">{icon}{label}</div>
      <div className="vbar-track flex-1 w-[26px]">
        <motion.div
          className={`vbar-fill ${fillClass[status.color]} ${flash}`}
          animate={{ height: `${pct}%` }}
          transition={{ type: "spring", stiffness: 120, damping: 20 }}
        />
      </div>
    </div>
  );
}
