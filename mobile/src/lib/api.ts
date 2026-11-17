// Talks to the Rootly server. The server's address comes from the file
// mobile/.env (EXPO_PUBLIC_API_URL).
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

export const API_URL = (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:5001').replace(/\/+$/, '');

const TOKEN_KEY = 'rootly_token';
let token: string | null = null;
let onLoggedOut: (() => void) | null = null;

/** Called when the server says our login is no longer valid. */
export function setLoggedOutHandler(handler: () => void) {
  onLoggedOut = handler;
}

// The login token is kept in the phone's secure storage (Keychain / Keystore).
// In a web browser, used only during development, it falls back to localStorage.
export async function loadToken(): Promise<string | null> {
  try {
    token =
      Platform.OS === 'web'
        ? globalThis.localStorage?.getItem(TOKEN_KEY) ?? null
        : await SecureStore.getItemAsync(TOKEN_KEY);
  } catch {
    token = null;
  }
  return token;
}

export async function saveToken(value: string | null) {
  token = value;
  try {
    if (Platform.OS === 'web') {
      if (value) globalThis.localStorage?.setItem(TOKEN_KEY, value);
      else globalThis.localStorage?.removeItem(TOKEN_KEY);
    } else if (value) {
      await SecureStore.setItemAsync(TOKEN_KEY, value);
    } else {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    }
  } catch {
    // Still logged in for this session even if it couldn't be saved
  }
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export type Photo = { uri: string; name?: string; type?: string };

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  /** Sent as JSON */
  body?: Record<string, unknown>;
  /** Sent as a form, for requests that carry a photo */
  form?: Record<string, string | string[] | Photo | null | undefined>;
};

function isPhoto(value: unknown): value is Photo {
  return typeof value === 'object' && value !== null && 'uri' in value;
}

async function buildForm(form: NonNullable<RequestOptions['form']>) {
  const data = new FormData();
  for (const [key, value] of Object.entries(form)) {
    if (value === null || value === undefined) continue;
    if (Array.isArray(value)) {
      value.forEach((item) => data.append(key, item));
    } else if (isPhoto(value)) {
      const name = value.name ?? 'photo.jpg';
      if (Platform.OS === 'web') {
        const blob = await (await fetch(value.uri)).blob();
        data.append(key, blob, name);
      } else {
        // React Native's way of attaching a file from the phone
        data.append(key, { uri: value.uri, name, type: value.type ?? 'image/jpeg' } as unknown as Blob);
      }
    } else {
      data.append(key, value);
    }
  }
  return data;
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  let payload: BodyInit | undefined;
  if (options.form) {
    payload = await buildForm(options.form);
  } else if (options.body) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(options.body);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1${path}`, {
      method: options.method ?? (payload ? 'POST' : 'GET'),
      headers,
      body: payload,
      signal: controller.signal,
    });
  } catch {
    throw new ApiError("Can't reach Rootly. Check your internet connection and try again.", 0);
  } finally {
    clearTimeout(timer);
  }

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // Not JSON (for example the server is restarting)
  }

  if (!response.ok) {
    const hadToken = Boolean(token);
    if (response.status === 401 && hadToken && !path.startsWith('/auth/')) {
      await saveToken(null);
      onLoggedOut?.();
    }
    throw new ApiError(data?.error ?? 'Something went wrong. Please try again.', response.status);
  }
  return data as T;
}

/** Photos we store come back as "/photos/abc.jpg"; plant database photos are full addresses. */
export function imageUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  return url.startsWith('/') ? `${API_URL}${url}` : url;
}
