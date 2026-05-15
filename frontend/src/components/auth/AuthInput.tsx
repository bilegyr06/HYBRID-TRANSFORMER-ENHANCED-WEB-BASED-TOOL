import type { ChangeEvent, InputHTMLAttributes, ReactNode } from 'react';

interface AuthInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  label: string;
  icon: ReactNode;
  name: string;
  value: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  labelAction?: ReactNode;
}

export default function AuthInput({
  label,
  icon,
  labelAction,
  className = '',
  ...inputProps
}: AuthInputProps) {
  return (
    <div>
      <div className={labelAction ? 'mb-1.5 flex items-center justify-between gap-3' : undefined}>
        <label className="mb-1.5 block text-[0.72rem] font-semibold tracking-[0.04em] text-[#d0d6e1] uppercase">
          {label}
        </label>
        {labelAction}
      </div>
      <div className="flex h-10 items-center gap-2 rounded-[2px] border border-[#39445d] bg-[#11172a] px-3 text-[#e4e7f0] transition focus-within:border-[#53e1de] focus-within:ring-1 focus-within:ring-[#53e1de]/30">
        {icon}
        <input
          {...inputProps}
          className={`w-full border-0 bg-transparent p-0 text-[0.9rem] text-[#e4e7f0] placeholder:text-[#6b7389] focus:outline-none focus:ring-0 ${className}`}
        />
      </div>
    </div>
  );
}
