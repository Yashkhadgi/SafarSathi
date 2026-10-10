import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiGet, apiPost, ApiError } from '../api/client';

export interface UserProfile {
  home_city?: string;
  diet_preference?: string;
  allergies?: string[];
  travel_style?: string;
  budget_range?: string;
  mobility_notes?: string;
  interests?: string[];
  consent_location?: boolean;
  consent_contacts?: boolean;
}

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  created_at: string;
  profile?: UserProfile | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<{ message: string }>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = async () => {
    try {
      const data = await apiGet<User>('/auth/me');
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await apiPost<{ user: User }>('/auth/login', { email, password });
    setUser(res.user);
  };

  const signup = async (email: string, password: string) => {
    return await apiPost<{ message: string; email: string; user_id: string }>('/auth/signup', {
      email,
      password,
    });
  };

  const logout = async () => {
    try {
      await apiPost('/auth/logout');
    } catch {
      // Ignore network errors on logout
    }
    setUser(null);
  };

  const refreshSession = async () => {
    try {
      await apiPost('/auth/refresh');
      await fetchCurrentUser();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setUser(null);
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
