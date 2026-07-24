import { AnimatePresence, motion } from "framer-motion";
import { TriangleAlert } from "lucide-react";

export default function WarningBanner({ message }) {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          data-testid="warning-banner"
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -50, opacity: 0 }}
          className="warn-banner absolute top-0 left-0 right-0 z-50 flex items-center justify-center gap-2 py-2 text-white font-bold tracking-widest text-[15px]"
        >
          <TriangleAlert size={18} strokeWidth={2.5} />
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
