import type { ReactNode } from 'react';
import { ChevronRight } from 'lucide-react';

interface DashboardCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  onClick: () => void;
}

export default function DashboardCard({ icon, title, description, onClick }: DashboardCardProps) {
  return (
    <button onClick={onClick} className="w-full border border-gray-800 rounded-lg p-6 sm:p-8 bg-gray-900 hover:border-teal-500 hover:bg-gray-850 transition text-left group">
      <div className="flex items-start justify-between">
        <div className="flex gap-4 flex-1">
          <div className="w-12 h-12 rounded-lg bg-gray-800 group-hover:bg-teal-900 transition flex items-center justify-center text-teal-400 flex-shrink-0">
            {icon}
          </div>
          <div>
            <h3 className="text-[0.95em] font-semibold text-white mb-1">{title}</h3>
            <p className="text-[0.85em] text-gray-400">{description}</p>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-gray-600 group-hover:text-teal-400 transition flex-shrink-0 ml-2" />
      </div>
    </button>
  );
}
