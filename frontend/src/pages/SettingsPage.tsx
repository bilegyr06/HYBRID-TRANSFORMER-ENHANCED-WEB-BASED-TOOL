interface DisplayUser {
  full_name: string;
  email: string;
  created_at: string;
}

interface SettingsPageProps {
  user: DisplayUser | null;
}

export default function SettingsPage({ user }: SettingsPageProps) {
  return (
    <div className="p-6 md:p-8 lg:p-10">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-[0.18em] text-teal-400 mb-2">Account</p>
        <h1 className="text-2xl md:text-3xl font-bold text-white">Settings</h1>
      </div>
      <div className="bg-gray-900/80 border border-gray-800/90 rounded-2xl p-6 max-w-2xl shadow-sm">
        <h2 className="text-base font-semibold mb-5">Account Information</h2>
        {user && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="text-[0.85em]">
              <p className="text-gray-500">Name</p>
              <p className="text-white font-semibold">{user.full_name}</p>
            </div>
            <div className="text-[0.85em]">
              <p className="text-gray-500">Email</p>
              <p className="text-white font-semibold">{user.email}</p>
            </div>
            <div className="text-[0.85em]">
              <p className="text-gray-500">Account Created</p>
              <p className="text-white font-semibold">{new Date(user.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        )}
        <h2 className="text-base font-semibold mt-8 mb-3">Preferences</h2>
        <p className="text-[0.85em] text-gray-400">Additional settings coming soon...</p>
      </div>
    </div>
  );
}
