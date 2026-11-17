import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Link } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { Body, Button, ErrorNote, Field, Screen } from '../components/ui';
import { useAuth } from '../lib/auth';
import { colors, serif, space } from '../lib/theme';

export default function Login() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await signIn(email.trim(), password);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not log in.');
      setBusy(false);
    }
  }

  return (
    <Screen>
      <View style={styles.hero}>
        <View style={styles.mark}>
          <Ionicons name="leaf" size={34} color={colors.cream} />
        </View>
        <Text style={styles.name} accessibilityRole="header">
          Rootly
        </Text>
        <Body muted style={{ textAlign: 'center' }}>
          Keep every plant you own watered, fed and thriving.
        </Body>
      </View>

      <ErrorNote message={error} />
      <Field
        label="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        textContentType="emailAddress"
        returnKeyType="next"
      />
      <Field
        label="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoComplete="current-password"
        textContentType="password"
        returnKeyType="go"
        onSubmitEditing={submit}
      />
      <Button label="Log in" onPress={submit} busy={busy} />

      <Link href="/register" style={styles.link}>
        New here? Create an account
      </Link>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: { alignItems: 'center', gap: space.sm, paddingTop: 72, paddingBottom: space.lg },
  mark: {
    width: 72,
    height: 72,
    borderRadius: 24,
    backgroundColor: colors.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  name: { fontFamily: serif, fontSize: 40, color: colors.forest },
  link: { textAlign: 'center', color: colors.leaf, fontSize: 16, fontWeight: '600', padding: space.md },
});
