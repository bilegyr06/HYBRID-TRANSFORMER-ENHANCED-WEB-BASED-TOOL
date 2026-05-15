import type { ReactNode } from 'react';

interface AuthShellProps {
  icon: ReactNode;
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}

export default function AuthShell({ icon, title, subtitle, children, footer }: AuthShellProps) {
  return (
    <div className="min-h-screen bg-[#050b19] text-white relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.08),_transparent_30%),radial-gradient(circle_at_bottom,_rgba(15,23,42,0.9),_transparent_45%)]" />
      <div className="absolute inset-0 opacity-40 bg-[linear-gradient(to_bottom,rgba(255,255,255,0.02),transparent_40%,rgba(255,255,255,0.01))]" />

      <div className="relative min-h-screen flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-[352px] rounded-[6px] border border-white/10 bg-[#252c40] shadow-[0_18px_50px_rgba(0,0,0,0.32)] px-7 py-8 sm:px-8 sm:py-9">
          <div className="flex flex-col items-center text-center">
            <div className="h-10 w-10 rounded-[3px] border border-white/10 bg-[#1a2134] flex items-center justify-center text-[#53e1de] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
              {icon}
            </div>
            <h1 className="mt-5 text-[1.9rem] leading-none font-medium tracking-[-0.04em] text-[#e8edf8]">{title}</h1>
            <p className="mt-2 text-[0.74rem] leading-5 text-[#b0b9ca] max-w-[240px]">{subtitle}</p>
          </div>

          <div className="mt-7">{children}</div>

          <div className="mt-7 border-t border-white/8 pt-4 text-center">{footer}</div>
        </div>
      </div>
    </div>
  );
}
