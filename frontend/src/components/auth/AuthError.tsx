interface AuthErrorProps {
  message?: string;
}

export default function AuthError({ message }: AuthErrorProps) {
  if (!message) return null;

  return (
    <div className="rounded-[3px] border border-red-500/20 bg-red-500/10 px-3 py-2">
      <p className="text-[0.75rem] font-medium text-red-200">{message}</p>
    </div>
  );
}
