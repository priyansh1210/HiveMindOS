import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { LiveToaster } from "@/components/layout/LiveToaster";
import { ToastProvider } from "@/lib/toast";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ToastProvider>
      <div className="flex min-h-screen w-full">
        <Sidebar />
        <div className="flex flex-1 flex-col min-w-0">
          <Header />
          <main className="flex-1 px-6 py-6 overflow-y-auto">{children}</main>
        </div>
      </div>
      <LiveToaster />
    </ToastProvider>
  );
}
