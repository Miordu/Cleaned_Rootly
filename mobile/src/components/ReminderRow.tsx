import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { api } from '../lib/api';
import { confirm } from '../lib/confirm';
import { daysUntil, dueLabel, todayISO } from '../lib/dates';
import { syncReminderNotifications } from '../lib/notifications';
import { colors, space } from '../lib/theme';
import type { Reminder } from '../lib/types';
import { Button } from './ui';

/** One reminder with a Done button. `showPlant` adds the plant's name (Today screen). */
export function ReminderRow({
  reminder,
  showPlant,
  onChanged,
  onOpenPlant,
}: {
  reminder: Reminder;
  showPlant?: boolean;
  onChanged: () => void;
  onOpenPlant?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const due = daysUntil(reminder.next_reminder_date) <= 0;

  async function done() {
    setBusy(true);
    try {
      await api(`/reminders/${reminder.reminder_id}/done`, { body: { today: todayISO() } });
      await syncReminderNotifications();
      onChanged();
    } catch {
      // The list reloads and shows the problem
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    const yes = await confirm(
      'Delete this reminder?',
      `You'll stop being reminded about ${reminder.reminder_type.toLowerCase()}.`,
      'Delete',
    );
    if (!yes) return;
    try {
      await api(`/reminders/${reminder.reminder_id}`, { method: 'DELETE' });
      await syncReminderNotifications();
    } finally {
      onChanged();
    }
  }

  return (
    <View style={styles.row}>
      <Pressable
        style={styles.text}
        disabled={!onOpenPlant}
        onPress={onOpenPlant}
        accessibilityRole={onOpenPlant ? 'button' : undefined}>
        <Text style={styles.type}>
          {reminder.reminder_type}
          {showPlant && reminder.plant_name ? ` · ${reminder.plant_name}` : ''}
        </Text>
        <Text style={[styles.when, due && { color: colors.terracotta, fontWeight: '600' }]}>
          {dueLabel(reminder.next_reminder_date)} · {reminder.frequency.toLowerCase()}
        </Text>
      </Pressable>
      <Button label="Done" icon="checkmark" small kind={due ? 'primary' : 'secondary'} busy={busy} onPress={done} />
      <Pressable
        onPress={remove}
        hitSlop={8}
        style={styles.remove}
        accessibilityRole="button"
        accessibilityLabel={`Delete ${reminder.reminder_type} reminder`}>
        <Ionicons name="trash-outline" size={20} color={colors.muted} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  text: { flex: 1, minHeight: 44, justifyContent: 'center' },
  type: { fontSize: 16, fontWeight: '600', color: colors.ink },
  when: { fontSize: 14, color: colors.muted, marginTop: 2 },
  remove: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
});
