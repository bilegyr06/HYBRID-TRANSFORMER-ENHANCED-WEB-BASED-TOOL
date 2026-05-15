/**
 * RegisterPage component for user account creation.
 * Supporting feature: User registration flow.
 */
import { useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, Sparkles, User } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import AuthShell from '../components/auth/AuthShell';
import AuthError from '../components/auth/AuthError';
import AuthInput from '../components/auth/AuthInput';
import AuthSubmitButton from '../components/auth/AuthSubmitButton';

interface RegisterFormState {
  email: string;
  password: string;
  confirmPassword: string;
  fullName: string;
}

export const RegisterPage = () => {
  const { register, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<RegisterFormState>({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [localError, setLocalError] = useState<string>('');

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setLocalError('');
  };

  const validateForm = (): boolean => {
    if (!formData.email || !formData.password || !formData.fullName) {
      setLocalError('Please fill in all fields');
      return false;
    }

    if (formData.password.length < 8) {
      setLocalError('Password must be at least 8 characters long');
      return false;
    }

    if (formData.password !== formData.confirmPassword) {
      setLocalError('Passwords do not match');
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setLocalError('Please enter a valid email address');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError('');

    if (!validateForm()) return;

    try {
      await register(formData.email, formData.password, formData.fullName);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Registration failed');
    }
  };

  return (
    <AuthShell
      icon={<Sparkles className="h-[18px] w-[18px]" />}
      title="Create an account"
      subtitle="Join LitReview AI to synthesize research faster."
      footer={(
        <p className="text-[0.75rem] text-[#b7c0d1]">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-medium text-[#53e1de] hover:text-[#71ece8]"
          >
            Sign in instead
          </Link>
        </p>
      )}
    >
      <form onSubmit={handleSubmit} className="space-y-3.5">
        <AuthInput
          label="Full name"
          icon={<User className="h-4 w-4 shrink-0 text-[#5d667d]" />}
          type="text"
          name="fullName"
          value={formData.fullName}
          onChange={handleChange}
          disabled={isLoading}
          placeholder="Dr. Jane Doe"
        />

        <AuthInput
          label="Email address"
          icon={<Mail className="h-4 w-4 shrink-0 text-[#5d667d]" />}
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          disabled={isLoading}
          placeholder="jane.doe@university.edu"
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
        />

        <AuthInput
          label="Confirm password"
          icon={<Lock className="h-4 w-4 shrink-0 text-[#5d667d]" />}
          type="password"
          name="confirmPassword"
          value={formData.confirmPassword}
          onChange={handleChange}
          disabled={isLoading}
          placeholder="••••••••"
        />

        <AuthError message={error || localError} />

        <AuthSubmitButton isLoading={isLoading} idleLabel="Create Account" loadingLabel="Creating account..." />
      </form>
    </AuthShell>
  );
};

export default RegisterPage;
