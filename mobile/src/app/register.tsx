import { useEffect, useState } from 'react';
import { Linking, Text } from 'react-native';

import { Button, Choices, ErrorNote, Field, Screen, Title } from '../components/ui';
import { API_URL, api } from '../lib/api';
import { useAuth } from '../lib/auth';
import { colors } from '../lib/theme';
import type { Options } from '../lib/types';

export default function Register() {
  const { signUp } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [region, setRegion] = useState<string | null>(null);
  const [options, setOptions] = useState<Options | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // The region list is optional, so a failure here is ignored
    api<Options>('/options').then(setOptions).catch(() => {});
  }, []);

  const minLength = options?.min_password_length ?? 8;

  async function submit() {
    if (!username.trim()) return setError('Choose a username.');
    if (!email.includes('@')) return setError('Enter a valid email address.');
    if (password.length < minLength) return setError(`Passwords need at least ${minLength} characters.`);
    setBusy(true);
    setError(null);
    try {
      await signUp({
        username: username.trim(),
        email: email.trim(),
        password,
        region_id: options?.regions.find((r) => r.name === region)?.region_id ?? null,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not create the account.');
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Title>Start your plant journal</Title>
      <ErrorNote message={error} />
      <Field label="Username" value={username} onChangeText={setUsername} autoCapitalize="none" autoComplete="username" />
      <Field
        label="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        textContentType="emailAddress"
      />
      <Field
        label="Password"
        hint={`At least ${minLength} characters`}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoComplete="new-password"
        textContentType="newPassword"
      />
      {options && options.regions.length > 0 ? (
        <Choices
          label="Where do you live? (optional)"
          options={options.regions.map((r) => r.name)}
          selected={region ? [region] : []}
          onToggle={(name) => setRegion(region === name ? null : name)}
        />
      ) : null}
      <Button label="Create account" onPress={submit} busy={busy} />
      <Text style={{ color: colors.muted, fontSize: 13, textAlign: 'center' }}>
        By creating an account you agree to how Rootly handles your data, described in the{' '}
        <Text
          accessibilityRole="link"
          style={{ color: colors.leaf, fontWeight: '600' }}
          onPress={() => Linking.openURL(`${API_URL}/privacy`)}>
          privacy page
        </Text>
        .
      </Text>
    </Screen>
  );
}
