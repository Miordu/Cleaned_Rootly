import { useCallback, useState } from 'react';
import { Linking } from 'react-native';
import { useFocusEffect } from 'expo-router';

import { Body, Button, Card, ErrorNote, Field, Screen, SectionTitle } from '../../components/ui';
import { API_URL } from '../../lib/api';
import { useAuth } from '../../lib/auth';
import { confirm } from '../../lib/confirm';
import { askForNotifications, notificationsAllowed, syncReminderNotifications } from '../../lib/notifications';

export default function Account() {
  const { user, signOut, deleteAccount } = useAuth();
  const [notifications, setNotifications] = useState<boolean | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      notificationsAllowed().then(setNotifications);
    }, []),
  );

  async function turnOnNotifications() {
    const allowed = await askForNotifications();
    setNotifications(allowed);
    if (allowed) await syncReminderNotifications();
    else Linking.openSettings().catch(() => {});
  }

  async function remove() {
    if (!password) return setError('Type your password to confirm.');
    const yes = await confirm(
      'Delete your account?',
      'Your plants, photos, care log and reminders will be deleted for good.',
      'Delete account',
    );
    if (!yes) return;
    setBusy(true);
    setError(null);
    try {
      await deleteAccount(password);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not delete the account.');
      setBusy(false);
    }
  }

  if (!user) return null;

  return (
    <Screen>
      <Card>
        <SectionTitle>{user.username}</SectionTitle>
        <Body muted>{user.email}</Body>
        {user.region ? <Body muted>{user.region}</Body> : null}
      </Card>

      <Card>
        <SectionTitle>Reminders</SectionTitle>
        {notifications ? (
          <Body muted>Notifications are on. You'll be reminded at 9 in the morning on the day care is due.</Body>
        ) : (
          <>
            <Body muted>Turn on notifications to be told when a plant needs care.</Body>
            <Button label="Turn on notifications" kind="secondary" icon="notifications-outline" onPress={turnOnNotifications} />
          </>
        )}
      </Card>

      <Button label="Privacy" kind="secondary" onPress={() => Linking.openURL(`${API_URL}/privacy`)} />
      <Button label="Log out" kind="secondary" icon="log-out-outline" onPress={signOut} />

      {deleting ? (
        <Card>
          <SectionTitle>Delete account</SectionTitle>
          <Body muted>This permanently deletes your account and everything in it. It cannot be undone.</Body>
          <ErrorNote message={error} />
          <Field label="Your password" value={password} onChangeText={setPassword} secureTextEntry autoComplete="current-password" />
          <Button label="Delete my account" kind="danger" busy={busy} onPress={remove} />
          <Button label="Cancel" kind="quiet" onPress={() => { setDeleting(false); setPassword(''); setError(null); }} />
        </Card>
      ) : (
        <Button label="Delete account" kind="quiet" onPress={() => setDeleting(true)} />
      )}
    </Screen>
  );
}
