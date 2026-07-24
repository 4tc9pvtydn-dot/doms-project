export default function PageIndicator({ count, index }) {
  return (
    <div className="flex items-center gap-[7px]" data-testid="page-indicator">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={`pdot ${i === index ? "active" : ""}`} data-testid={`page-dot-${i}`} />
      ))}
    </div>
  );
}
