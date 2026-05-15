import { Menu, X } from 'lucide-react';

interface MobileTopBarProps {
  isOpen: boolean;
  onToggle: () => void;
}

export default function MobileTopBar({ isOpen, onToggle }: MobileTopBarProps) {
  return (
    <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-gray-900/95 border-b border-gray-800/80 px-4 py-2 flex items-center justify-between backdrop-blur" style={{ height: '56px' }}>
      <div className="text-[0.9em] font-bold text-white">LitReview <span className="text-teal-400">AI</span></div>
      <button
        onClick={onToggle}
        className="text-gray-400 hover:text-white transition"
        aria-label="Toggle menu"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>
    </div>
  );
}
