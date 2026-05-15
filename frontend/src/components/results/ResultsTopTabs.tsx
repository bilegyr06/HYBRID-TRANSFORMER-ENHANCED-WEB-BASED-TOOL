import type { ViewTab } from '../../lib/results';

interface ResultsTopTabsProps {
  activeTab: ViewTab;
  onTabChange: (tab: ViewTab) => void;
}

export default function ResultsTopTabs({ activeTab, onTabChange }: ResultsTopTabsProps) {
  return (
    <div className="flex gap-2 mt-6 mb-6 border-b border-gray-800">
      {[
        ['synthesis', 'Overall Synthesis'],
        ['results', 'Individual Results'],
      ].map(([tab, label]) => (
        <button
          key={tab}
          onClick={() => onTabChange(tab as ViewTab)}
          className={`py-3 sm:py-4 px-3 sm:px-6 font-medium transition text-sm sm:text-base ${
            activeTab === tab
              ? 'text-teal-400 border-b-2 border-teal-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
