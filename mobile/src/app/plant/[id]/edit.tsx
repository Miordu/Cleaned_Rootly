import { useEffect, useState } from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { Button, Choices, ErrorNote, Field, LoadProblem, Loading, PlantImage, Screen } from '../../../components/ui';
import { api, type Photo } from '../../../lib/api';
import { confirm } from '../../../lib/confirm';
import { syncReminderNotifications } from '../../../lib/notifications';
import { pickPhoto } from '../../../lib/pickPhoto';
import type { MyPlant } from '../../../lib/types';

const STATUSES = ['active', 'dormant', 'struggling', 'deceased'];

export default function EditPlant() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [plant, setPlant] = useState<MyPlant | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [nickname, setNickname] = useState('');
  const [location, setLocation] = useState('');
  const [status, setStatus] = useState('active');
  const [notes, setNotes] = useState('');
  const [photo, setPhoto] = useState<Photo | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Loaded once (not on every focus) so typing isn't overwritten after picking a photo
  async function load() {
    setLoadError(null);
    try {
      const { plant: loaded } = await api<{ plant: MyPlant }>(`/my-plants/${id}`);
      setPlant(loaded);
      setNickname(loaded.nickname ?? '');
      setLocation(loaded.location ?? '');
      setStatus(loaded.status ?? 'active');
      setNotes(loaded.notes ?? '');
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : 'Could not load the plant.');
    }
  }
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      await api(`/my-plants/${id}`, { form: { nickname, location, status, notes, image: photo } });
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save.');
      setBusy(false);
    }
  }

  async function remove() {
    const yes = await confirm(
      `Remove ${plant?.name ?? 'this plant'}?`,
      'Its care log, reminders and health records will be deleted too.',
      'Remove',
    );
    if (!yes) return;
    setBusy(true);
    try {
      await api(`/my-plants/${id}`, { method: 'DELETE' });
      await syncReminderNotifications();
      router.dismissTo('/plants');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not remove the plant.');
      setBusy(false);
    }
  }

  if (loadError) return <LoadProblem message={loadError} onRetry={load} />;
  if (!plant) return <Loading />;

  return (
    <Screen footer={<Button label="Save changes" onPress={save} busy={busy} />}>
      <ErrorNote message={error} />
      <PlantImage url={photo?.uri ?? plant.image_url} style={{ width: '100%', aspectRatio: 4 / 3, borderRadius: 22 }} label="Plant photo" />
      <Button
        label={plant.has_own_photo || photo ? 'Change photo' : 'Add your own photo'}
        icon="camera-outline"
        kind="secondary"
        onPress={async () => {
          const picked = await pickPhoto();
          if (picked) setPhoto(picked);
        }}
      />
      <Field label="Nickname" value={nickname} onChangeText={setNickname} maxLength={100} />
      <Field label="Where is it?" value={location} onChangeText={setLocation} maxLength={100} />
      <Choices label="How is it doing?" options={STATUSES} selected={[status]} onToggle={setStatus} />
      <Field label="Notes" value={notes} onChangeText={setNotes} multiline />
      <Button label="Remove from my plants" kind="danger" icon="trash-outline" onPress={remove} />
    </Screen>
  );
}
