import { BookOpen, Settings, Upload } from 'lucide-react';
import type { AppPage } from '../components/layout/appNavigation';

interface DisplayUser {
  full_name: string;
}

interface DashboardPageProps {
  user: DisplayUser | null;
  onNavigate: (page: AppPage) => void;
}

export default function DashboardPage({ user, onNavigate }: DashboardPageProps) {
  const cards = [
    {
      title: 'Upload & Process',
      description: 'Add new academic papers and generate synthesis',
      page: 'upload' as const,
      icon: Upload,
    },
    {
      title: 'My Reviews',
      description: 'Access saved literature reviews',
      page: 'my-reviews' as const,
      icon: BookOpen,
    },
    {
      title: 'Settings',
      description: 'Configure your preferences',
      page: 'settings' as const,
      icon: Settings,
    },
  ];

  return (
    <div className="p-6 md:p-8 lg:p-10">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-[0.18em] text-teal-400 mb-2">Workspace</p>
        <h1 className="text-2xl md:text-3xl font-bold text-white">Dashboard</h1>
      </div>
      {user && (
        <p className="text-[0.95em] text-gray-400 -mt-5 mb-8">
          Welcome back, <span className="text-teal-300 font-semibold">{user.full_name}</span>.
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 xl:gap-6">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <button
              key={card.page}
              onClick={() => onNavigate(card.page)}
              className="text-left bg-gray-900/80 border border-gray-800/90 rounded-2xl p-6 cursor-pointer hover:border-teal-500/60 hover:bg-gray-900 transition shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40"
            >
              <div className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-300">
                <Icon size={24} />
              </div>
              <h2 className="text-base font-semibold mb-2 text-white">{card.title}</h2>
              <p className="text-sm leading-6 text-gray-400">{card.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
