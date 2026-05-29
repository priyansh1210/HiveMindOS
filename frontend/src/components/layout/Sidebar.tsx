import Link from "next/link";

const navItems = [
  { href: "/dashboard", label: "Agents", icon: "◎" },
  { href: "/dashboard/bots", label: "Bots", icon: "✸" },
  { href: "/dashboard/tasks", label: "Tasks", icon: "▤" },
  { href: "/dashboard/chat", label: "Chat", icon: "✦" },
  { href: "/dashboard/analytics", label: "Analytics", icon: "▲" },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r border-zinc-800 bg-zinc-950 px-4 py-6 flex flex-col gap-1">
      <div className="px-2 pb-6">
        <div className="text-xs uppercase tracking-wider text-zinc-500">
          NovaTech
        </div>
        <div className="text-base font-semibold text-zinc-100">
          AI Workforce
        </div>
      </div>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-900 hover:text-white transition-colors"
          >
            <span className="text-zinc-500 w-4 text-center">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="mt-auto px-2 pt-6 text-xs text-zinc-600">
        v0.1 · Phase 2 Day 4
      </div>
    </aside>
  );
}
