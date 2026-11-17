import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { api, loadToken, saveToken, setLoggedOutHandler } from './api';
import { clearReminderNotifications } from './notifications';
import type { User } from './types';

type AuthState = {
  /** null while logged out */
  user: User | null;
  /** true while we check for a saved login at start-up */
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (details: { username: string; email: string; password: string; region_id?: number | null }) => Promise<void>;
  signOut: () => Promise<void>;
  deleteAccount: (password: string) => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

type Session = { token: string; user: User };

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoggedOutHandler(() => setUser(null));
    (async () => {
      if (await loadToken()) {
        try {
          setUser((await api<{ user: User }>('/me')).user);
        } catch {
          // No connection or the login expired: show the login screen
        }
      }
      setLoading(false);
    })();
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const session = await api<Session>('/auth/login', { body: { email, password } });
    await saveToken(session.token);
    setUser(session.user);
  }, []);

  const signUp = useCallback<AuthState['signUp']>(async (details) => {
    const session = await api<Session>('/auth/register', { body: details });
    await saveToken(session.token);
    setUser(session.user);
  }, []);

  const forget = useCallback(async () => {
    await saveToken(null);
    await clearReminderNotifications();
    setUser(null);
  }, []);

  const signOut = useCallback(async () => {
    try {
      await api('/auth/logout', { method: 'POST' });
    } catch {
      // Logging out on this phone still works without a connection
    }
    await forget();
  }, [forget]);

  const deleteAccount = useCallback(
    async (password: string) => {
      await api('/me', { method: 'DELETE', body: { password } });
      await forget();
    },
    [forget],
  );

  const value = useMemo(
    () => ({ user, loading, signIn, signUp, signOut, deleteAccount }),
    [user, loading, signIn, signUp, signOut, deleteAccount],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
