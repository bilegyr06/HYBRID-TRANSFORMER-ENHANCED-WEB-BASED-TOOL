import { LogOut } from 'lucide-react';
import { navItems, type AppPage } from './appNavigation';

interface MobileNavMenuProps {
  isOpen: boolean;
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
  onLogout: () => void;
}

export default function MobileNavMenu({
  isOpen,
  activePage,
  onNavigate,
  onLogout,
}: MobileNavMenuProps) {
  if (!isOpen) return null;

  return (
    <div className="md:hidden fixed top-14 left-0 right-0 bg-gray-900/95 border-b border-gray-800/80 z-40 backdrop-blur">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = activePage === item.page;

        return (
          <button
            key={item.page}
            onClick={() => onNavigate(item.page)}
            className={`w-full text-left px-4 py-3 border-b border-gray-800/80 transition flex items-center gap-3 ${
              isActive
                ? 'text-teal-300 bg-teal-500/10 font-medium'
                : 'text-gray-300 hover:bg-gray-800/70'
            }`}
          >
            <Icon size={18} />
            <span className="text-[0.85em]">{item.label}</span>
          </button>
        );
      })}
      <button
        onClick={onLogout}
        className="w-full text-left px-4 py-3 border-t border-gray-800/80 text-red-300 hover:bg-red-500/10 transition flex items-center gap-3"
      >
        <LogOut size={18} />
        <span className="text-[0.85em]">Logout</span>
      </button>
    </div>
  );
}
