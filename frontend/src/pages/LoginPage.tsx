/**
 * LoginPage component for user authentication.
 * Supporting feature: User authentication flow.
 */
import { useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Lock, Mail } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import AuthShell from '../components/auth/AuthShell';
import AuthError from '../components/auth/AuthError';
import AuthInput from '../components/auth/AuthInput';
import AuthSubmitButton from '../components/auth/AuthSubmitButton';

interface LoginFormState {
  email: string;
  password: string;
}

export const LoginPage = () => {
  const { login, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<LoginFormState>({ email: '', password: '' });
  const [localError, setLocalError] = useState<string>('');

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setLocalError('');
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLocalError('');

    if (!formData.email || !formData.password) {
      setLocalError('Please fill in all fields');
      return;
    }

    try {
      await login(formData.email, formData.password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <AuthShell
      icon={<BookOpen className="h-[18px] w-[18px]" />}
      title="LitReview AI"
      subtitle="Sign in to continue your research."
      footer={(
        <p className="text-[0.75rem] text-[#b7c0d1]">
          Don&apos;t have an account?{' '}
          <Link
            to="/register"
            className="font-medium text-[#53e1de] hover:text-[#71ece8]"
          >
            Create an account
          </Link>
        </p>
      )}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthInput
          label="Email address"
          icon={<Mail className="h-4 w-4 shrink-0 text-[#5d667d]" />}
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          disabled={isLoading}
          placeholder="dr.smith@university.edu"
        />

        <AuthInput
          label="Password"
          icon={<Lock className="h-4 w-4 shrink-0 text-[#5d667d]" />}
          type="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          disabled={isLoading}
          placeholder="••••••••"
          labelAction={(
            <a
              href="/forgot-password"
              className="text-[0.65rem] font-medium leading-none text-[#53e1de] visited:text-[#7aa6ff] hover:text-[#71ece8] active:text-[#9ef3ef] focus:text-[#71ece8] focus:outline-none"
            >
              Forgot?
            </a>
          )}
        />

        <AuthError message={error || localError} />

        <AuthSubmitButton isLoading={isLoading} idleLabel="Sign In" loadingLabel="Signing in..." />
      </form>
    </AuthShell>
  );
};

export default LoginPage;
