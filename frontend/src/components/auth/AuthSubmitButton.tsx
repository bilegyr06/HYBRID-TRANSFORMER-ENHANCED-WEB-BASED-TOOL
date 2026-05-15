import { ArrowRightIcon, Loader2 } from 'lucide-react';

interface AuthSubmitButtonProps {
  isLoading: boolean;
  idleLabel: string;
  loadingLabel: string;
}

export default function AuthSubmitButton({
  isLoading,
  idleLabel,
  loadingLabel,
}: AuthSubmitButtonProps) {
  return (
    <button
      type="submit"
      disabled={isLoading}
      className="mt-2 flex h-10 w-full items-center justify-center gap-2 rounded-[2px] !bg-[#53e1de] !text-[#0a1020] transition hover:!bg-[#61e8e4] disabled:cursor-not-allowed disabled:opacity-60"
    >
      {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
      {isLoading ? loadingLabel : idleLabel}
      {!isLoading && <ArrowRightIcon className="h-4 w-4" />}
    </button>
  );
}
