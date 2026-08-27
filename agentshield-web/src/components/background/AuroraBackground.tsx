export function AuroraBackground() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-grid-fade opacity-60" />
      <div className="absolute -left-40 top-[-10%] h-[46rem] w-[46rem] rounded-full bg-neon-blue/25 blur-[130px] animate-aurora" />
      <div className="absolute right-[-12%] top-[6%] h-[40rem] w-[40rem] rounded-full bg-neon-violet/25 blur-[140px] animate-aurora [animation-delay:-6s]" />
      <div className="absolute bottom-[-18%] left-1/3 h-[36rem] w-[36rem] rounded-full bg-neon-cyan/15 blur-[150px] animate-aurora [animation-delay:-10s]" />
    </div>
  );
}
