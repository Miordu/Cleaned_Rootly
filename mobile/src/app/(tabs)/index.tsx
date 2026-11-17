import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { ReminderRow } from '../../components/ReminderRow';
import { Body, Button, Card, Empty, LoadProblem, Loading, Screen, SectionTitle, Title } from '../../components/ui';
import { api } from '../../lib/api';
import { daysUntil } from '../../lib/dates';
import { askForNotifications, syncReminderNotifications } from '../../lib/notifications';
import { colors, serif, space } from '../../lib/theme';
import { useLoad } from '../../lib/useLoad';
import type { Dashboard, Reminder } from '../../lib/types';

type HomeData = { dashboard: Dashboard; reminders: Reminder[] };

export default function Today() {
  const router = useRouter();
  const { data, error, loading, refreshing, reload } = useLoad<HomeData>(async () => {
    const [dashboard, list] = await Promise.all([
      api<Dashboard>('/dashboard'),
      api<{ reminders: Reminder[] }>('/reminders'),
    ]);
    return { dashboard, reminders: list.reminders };
  });

  const hasReminders = (data?.reminders.length ?? 0) > 0;
  useEffect(() => {
    // Ask to send notifications only once there is something to be reminded of
    if (hasReminders) {
      askForNotifications().then((allowed) => {
        if (allowed) syncReminderNotifications(data?.reminders);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasReminders]);

  if (loading) return <Loading />;
  if (!data) return <LoadProblem message={error ?? ''} onRetry={() => reload(true)} />;

  const { dashboard, reminders } = data;
  const due = reminders.filter((r) => daysUntil(r.next_reminder_date) <= 0);
  const soon = reminders.filter((r) => {
    const days = daysUntil(r.next_reminder_date);
    return days > 0 && days <= 7;
  });
  const open = (r: Reminder) => () => router.push(`/plant/${r.user_plant_id}`);

  return (
    <Screen onRefresh={() => reload(true)} refreshing={refreshing}>
      <View>
        <Title>Hello, {dashboard.user.username}</Title>
        <Body muted>
          {due.length === 0
            ? 'Nothing needs doing right now.'
            : due.length === 1
              ? '1 plant needs you today.'
              : `${due.length} things to do today.`}
        </Body>
      </View>

      <View style={styles.stats}>
        <Stat value={dashboard.plant_count} label={dashboard.plant_count === 1 ? 'plant' : 'plants'} />
        <Stat value={due.length} label="due now" warm={due.length > 0} />
        <Stat value={dashboard.recent_care_count} label="cared for this month" />
      </View>

      {dashboard.plant_count === 0 ? (
        <Empty icon="leaf-outline" title="Add your first plant" text="Search for it by name, then set a reminder so you never forget to water it.">
          <Button label="Add a plant" icon="add" onPress={() => router.push('/add-plant')} />
        </Empty>
      ) : null}

      {due.length > 0 ? (
        <>
          <SectionTitle>Due now</SectionTitle>
          <Card style={{ borderColor: colors.terracotta }}>
            {due.map((r) => (
              <ReminderRow key={r.reminder_id} reminder={r} showPlant onChanged={reload} onOpenPlant={open(r)} />
            ))}
          </Card>
        </>
      ) : null}

      {soon.length > 0 ? (
        <>
          <SectionTitle>Coming up this week</SectionTitle>
          <Card>
            {soon.map((r) => (
              <ReminderRow key={r.reminder_id} reminder={r} showPlant onChanged={reload} onOpenPlant={open(r)} />
            ))}
          </Card>
        </>
      ) : null}

      {dashboard.plant_count > 0 && reminders.length === 0 ? (
        <Empty
          icon="notifications-outline"
          title="No reminders yet"
          text="Open one of your plants and add a reminder to be told when it needs water."
        >
          <Button label="Go to my plants" kind="secondary" onPress={() => router.push('/plants')} />
        </Empty>
      ) : null}
    </Screen>
  );
}

function Stat({ value, label, warm }: { value: number; label: string; warm?: boolean }) {
  return (
    <View style={[styles.stat, warm && { backgroundColor: colors.terracottaSoft }]} accessible accessibilityLabel={`${value} ${label}`}>
      <Text style={[styles.statValue, warm && { color: colors.terracotta }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  stats: { flexDirection: 'row', gap: space.sm },
  stat: { flex: 1, backgroundColor: colors.sage, borderRadius: 14, padding: space.md, minHeight: 84 },
  statValue: { fontFamily: serif, fontSize: 30, color: colors.forest, fontVariant: ['tabular-nums'] },
  statLabel: { fontSize: 13, color: colors.forest },
});
