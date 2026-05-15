import { LogOut } from 'lucide-react';
import { navItems, type AppPage } from './appNavigation';

interface DisplayUser {
  full_name: string;
  email: string;
}

interface DesktopSidebarProps {
  user: DisplayUser | null;
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
  onLogout: () => void;
}

export default function DesktopSidebar({
  user,
  activePage,
  onNavigate,
  onLogout,
}: DesktopSidebarProps) {
  return (
    <div className="hidden md:flex md:flex-col md:w-60 bg-gray-900/95 border-r border-gray-800/80 sticky top-0 h-screen">
      <div className="p-6 border-b border-gray-800/80">
        <h2 className="text-[1.75em] leading-tight font-bold text-white">
          LitReview <span className="text-teal-400">AI</span>
        </h2>
        <p className="text-[0.7em] uppercase tracking-[0.18em] text-gray-500 mt-2">Academic Synthesis</p>
      </div>

      {user && (
        <div className="mx-4 mt-4 rounded-xl border border-gray-800 bg-gray-950/45 px-4 py-4">
          <p className="text-[0.7em] uppercase tracking-[0.14em] text-gray-500">Logged in as</p>
          <p className="text-[0.9em] font-semibold text-white truncate">{user.full_name}</p>
          <p className="text-[0.75em] text-gray-500 truncate mt-0.5">{user.email}</p>
        </div>
      )}

      <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.page;

          return (
            <button
              key={item.page}
              onClick={() => onNavigate(item.page)}
              className={`w-full text-left px-4 py-3 rounded-xl transition flex items-center gap-3 border ${
                isActive
                  ? 'text-teal-300 bg-teal-500/10 border-teal-500/25 font-medium'
                  : 'text-gray-400 border-transparent hover:text-white hover:bg-gray-800/70'
              }`}
            >
              <Icon size={16} />
              <span className="text-[0.85em]">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="border-t border-gray-800/80 p-4 space-y-3">
        <button
          onClick={onLogout}
          className="w-full text-left px-4 py-2.5 rounded-xl text-red-300 hover:bg-red-500/10 transition flex items-center gap-2 text-[0.85em]"
        >
          <LogOut size={16} />
          <span>Logout</span>
        </button>
        <p className="text-[0.75em] text-gray-500">v1.0 - TextRank + BART</p>
      </div>
    </div>
  );
}
