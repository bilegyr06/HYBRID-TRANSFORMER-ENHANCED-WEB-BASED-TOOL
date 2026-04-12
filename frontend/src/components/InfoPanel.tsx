import { Info } from 'lucide-react';

interface StepContent { step: number; text: string; }
interface InfoPanelProps { title: string; content: string | StepContent[]; }

export default function InfoPanel({ title, content }: InfoPanelProps) {
  const isStepContent = Array.isArray(content);

  return (
    <div className="border border-gray-800 rounded-lg bg-gray-900 overflow-hidden">
      <div className="border-b border-gray-800 p-4 sm:p-6 bg-gray-950">
        <div className="flex items-center gap-3">
          <Info className="w-5 h-5 text-teal-400 flex-shrink-0" />
          <h3 className="text-[0.95em] sm:text-[1.05em] font-semibold text-white">{title}</h3>
        </div>
      </div>

      <div className="p-4 sm:p-6">
        {isStepContent ? (
          <div className="space-y-4">
            {content.map((item, idx) => (
              <div key={idx} className="flex gap-3">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-teal-900 flex-shrink-0">
                  <span className="text-[0.85em] font-semibold text-teal-300">{item.step}</span>
                </div>
                <p className="text-[0.9em] text-gray-300 leading-relaxed pt-0.5">{item.text}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[0.9em] text-gray-300 leading-relaxed whitespace-pre-wrap">{content}</p>
        )}
      </div>
    </div>
  );
}
