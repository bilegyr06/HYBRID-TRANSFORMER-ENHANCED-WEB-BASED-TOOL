import { BookOpen, FileText, Settings, Upload } from 'lucide-react';

export type AppPage = 'dashboard' | 'upload' | 'results' | 'my-reviews' | 'settings';

export const APP_PATHS: Record<AppPage, string> = {
  dashboard: '/dashboard',
  upload: '/upload',
  results: '/results',
  'my-reviews': '/my-reviews',
  settings: '/settings',
};

export const navItems = [
  { label: 'Dashboard', page: 'dashboard' as const, icon: FileText },
  { label: 'Upload & Process', page: 'upload' as const, icon: Upload },
  { label: 'My Reviews', page: 'my-reviews' as const, icon: BookOpen },
  { label: 'Settings', page: 'settings' as const, icon: Settings },
];

export function getAppPage(pathname: string): AppPage {
  if (pathname.startsWith('/upload')) return 'upload';
  if (pathname.startsWith('/results')) return 'results';
  if (pathname.startsWith('/my-reviews')) return 'my-reviews';
  if (pathname.startsWith('/settings')) return 'settings';
  return 'dashboard';
}
