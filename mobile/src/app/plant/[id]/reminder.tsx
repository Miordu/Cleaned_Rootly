import { useEffect, useState } from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { Button, Choices, ErrorNote, Screen } from '../../../components/ui';
import { api } from '../../../lib/api';
import { addDays, toISODate } from '../../../lib/dates';
import { askForNotifications, syncReminderNotifications } from '../../../lib/notifications';
import type { Options } from '../../../lib/types';

const TYPES = ['Watering', 'Fertilizing', 'Pruning', 'Repotting', 'Misting', 'Other'];
const FREQUENCIES = ['Daily', 'Weekly', 'Biweekly', 'Monthly', 'Seasonally'];
const STARTS: Record<string, number> = { Today: 0, Tomorrow: 1, 'In 3 days': 3, 'In a week': 7, 'In 2 weeks': 14 };

export default function NewReminder() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [types, setTypes] = useState(TYPES);
  const [frequencies, setFrequencies] = useState(FREQUENCIES);
  const [type, setType] = useState('Watering');
  const [frequency, setFrequency] = useState('Weekly');
  const [start, setStart] = useState('In a week');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Options>('/options')
      .then((o) => {
        setTypes(o.care_types);
        setFrequencies(o.reminder_frequencies);
      })
      .catch(() => {});
  }, []);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      await api(`/my-plants/${id}/reminders`, {
        body: {
          reminder_type: type,
          frequency,
          next_reminder_date: toISODate(addDays(STARTS[start])),
        },
      });
      if (await askForNotifications()) await syncReminderNotifications();
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save.');
      setBusy(false);
    }
  }

  return (
    <Screen footer={<Button label="Save reminder" onPress={save} busy={busy} />}>
      <ErrorNote message={error} />
      <Choices label="Remind me about" options={types} selected={[type]} onToggle={setType} />
      <Choices label="How often" options={frequencies} selected={[frequency]} onToggle={setFrequency} />
      <Choices label="Starting" options={Object.keys(STARTS)} selected={[start]} onToggle={setStart} />
    </Screen>
  );
}
