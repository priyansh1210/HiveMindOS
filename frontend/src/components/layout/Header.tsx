import { BackendStatus } from "./BackendStatus";

export function Header() {
  return (
    <header className="h-14 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur px-6 flex items-center justify-between">
      <div>
        <h1 className="text-sm font-semibold text-zinc-100">Dashboard</h1>
        <p className="text-xs text-zinc-500">
          Five autonomous agents · NovaTech Inc.
        </p>
      </div>
      <BackendStatus />
    </header>
  );
}
