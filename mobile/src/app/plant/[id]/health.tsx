import { useState } from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { Button, Choices, ErrorNote, Field, PlantImage, Screen } from '../../../components/ui';
import { api, type Photo } from '../../../lib/api';
import { pickPhoto } from '../../../lib/pickPhoto';

const SYMPTOMS = ['Yellow leaves', 'Brown leaf tips', 'Wilting', 'Leaf spots', 'Drooping', 'Pests visible'];

export default function HealthCheck() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [diagnosis, setDiagnosis] = useState('');
  const [treatment, setTreatment] = useState('');
  const [photo, setPhoto] = useState<Photo | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggle(symptom: string) {
    setSymptoms((current) =>
      current.includes(symptom) ? current.filter((s) => s !== symptom) : [...current, symptom],
    );
  }

  async function save() {
    if (!diagnosis.trim() && symptoms.length === 0) {
      return setError("Pick at least one symptom or say what you think is wrong.");
    }
    setBusy(true);
    setError(null);
    try {
      await api(`/my-plants/${id}/health`, {
        form: {
          symptoms,
          diagnosis: diagnosis.trim(),
          treatment_recommendations: treatment.trim(),
          image: photo,
        },
      });
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save.');
      setBusy(false);
    }
  }

  return (
    <Screen footer={<Button label="Save health record" onPress={save} busy={busy} />}>
      <ErrorNote message={error} />
      <Choices label="What do you see?" options={SYMPTOMS} selected={symptoms} onToggle={toggle} />
      <Field label="What do you think is wrong?" value={diagnosis} onChangeText={setDiagnosis} placeholder="e.g. Overwatering" maxLength={255} />
      <Field label="What will you do about it?" value={treatment} onChangeText={setTreatment} multiline placeholder="e.g. Let the soil dry out before watering again" />
      {photo ? <PlantImage url={photo.uri} style={{ width: '100%', aspectRatio: 4 / 3, borderRadius: 14 }} label="Chosen photo" /> : null}
      <Button
        label={photo ? 'Change photo' : 'Add a photo (optional)'}
        icon="camera-outline"
        kind="secondary"
        onPress={async () => {
          const picked = await pickPhoto();
          if (picked) setPhoto(picked);
        }}
      />
    </Screen>
  );
}
