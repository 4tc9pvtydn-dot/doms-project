import { motion } from "framer-motion";

export default function StartupScreen() {
  return (
    <div
      className="carbon absolute inset-0 flex flex-col items-center justify-center"
      data-testid="startup-screen"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="text-center"
      >
        <div
          className="digital text-[46px] font-black tracking-[0.15em]"
          style={{ textShadow: "0 0 18px rgba(255,255,255,0.35)" }}
        >
          DOMS
        </div>
        <div className="digital text-[30px] font-extrabold tracking-[0.4em] t-amber mt-1">
          RB252
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-10 w-[260px]"
      >
        <div className="text-center text-[12px] tracking-[0.3em] t-dim mb-2">
          INITIALISING&hellip;
        </div>
        <div className="h-[6px] w-full rounded-full bg-[#1c1d21] overflow-hidden">
          <div className="boot-fill h-full rounded-full bg-gradient-to-r from-amber-400 to-red-500" />
        </div>
      </motion.div>
    </div>
  );
}
