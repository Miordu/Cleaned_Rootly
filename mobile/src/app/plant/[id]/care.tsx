import { useEffect, useState } from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { Button, Choices, ErrorNote, Field, Screen } from '../../../components/ui';
import { api } from '../../../lib/api';
import type { Options } from '../../../lib/types';

const FALLBACK = ['Watering', 'Fertilizing', 'Pruning', 'Repotting', 'Misting', 'Other'];

export default function LogCare() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [types, setTypes] = useState(FALLBACK);
  const [type, setType] = useState('Watering');
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Options>('/options').then((o) => setTypes(o.care_types)).catch(() => {});
  }, []);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      await api(`/my-plants/${id}/care-events`, { body: { event_type: type, notes } });
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save.');
      setBusy(false);
    }
  }

  return (
    <Screen footer={<Button label="Save" onPress={save} busy={busy} />}>
      <ErrorNote message={error} />
      <Choices label="What did you do?" options={types} selected={[type]} onToggle={setType} />
      <Field label="Notes (optional)" value={notes} onChangeText={setNotes} multiline placeholder="e.g. Used rainwater" />
    </Screen>
  );
}
