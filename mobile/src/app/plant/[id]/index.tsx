import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { ReminderRow } from '../../../components/ReminderRow';
import { Body, Button, Card, LoadProblem, Loading, PlantImage, Screen, SectionTitle, Tag, Title } from '../../../components/ui';
import { api } from '../../../lib/api';
import { shortDate } from '../../../lib/dates';
import { colors, space } from '../../../lib/theme';
import { useLoad } from '../../../lib/useLoad';
import type { Care, HealthAssessment, MyPlant } from '../../../lib/types';

export default function PlantScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { data: plant, error, loading, refreshing, reload } = useLoad(
    async () => (await api<{ plant: MyPlant }>(`/my-plants/${id}`)).plant,
  );

  if (loading) return <Loading />;
  if (!plant) return <LoadProblem message={error ?? ''} onRetry={() => reload(true)} />;

  const reminders = plant.reminders ?? [];
  const events = plant.care_events ?? [];
  const health = plant.health_assessments ?? [];
  const toxic = plant.plant.poisonous_to_pets || plant.plant.poisonous_to_humans;

  return (
    <Screen onRefresh={() => reload(true)} refreshing={refreshing}>
      <PlantImage url={plant.image_url} style={styles.hero} label={`Photo of ${plant.name}`} />

      <View style={{ gap: 4 }}>
        <Title>{plant.name}</Title>
        <Text style={styles.scientific}>{plant.plant.scientific_name}</Text>
        <View style={styles.tags}>
          {plant.location ? <Tag label={plant.location} /> : null}
          {plant.status && plant.status !== 'active' ? <Tag label={plant.status} tone="warm" /> : null}
          {toxic ? <Tag label="Poisonous" tone="warm" /> : null}
        </View>
      </View>

      <View style={styles.actions}>
        <Button label="Log care" icon="water-outline" style={styles.action} onPress={() => router.push(`/plant/${id}/care`)} />
        <Button label="Health" icon="medkit-outline" kind="secondary" style={styles.action} onPress={() => router.push(`/plant/${id}/health`)} />
        <Button label="Edit" icon="create-outline" kind="secondary" style={styles.action} onPress={() => router.push(`/plant/${id}/edit`)} />
      </View>

      <SectionTitle>Reminders</SectionTitle>
      <Card>
        {reminders.length === 0 ? <Body muted>No reminders yet.</Body> : null}
        {reminders.map((r) => (
          <ReminderRow key={r.reminder_id} reminder={r} onChanged={reload} />
        ))}
        <Button label="Add a reminder" icon="add" kind="secondary" onPress={() => router.push(`/plant/${id}/reminder`)} />
      </Card>

      {plant.notes ? (
        <>
          <SectionTitle>Your notes</SectionTitle>
          <Card>
            <Body>{plant.notes}</Body>
          </Card>
        </>
      ) : null}

      <SectionTitle>Care guide</SectionTitle>
      <Card>
        {plant.plant.description ? <Body>{plant.plant.description}</Body> : null}
        <CareGuide care={plant.plant.care} />
      </Card>

      {health.length > 0 ? (
        <>
          <SectionTitle>Health records</SectionTitle>
          {health.map((record) => (
            <HealthCard key={record.assessment_id} record={record} onChanged={reload} />
          ))}
        </>
      ) : null}

      <SectionTitle>Care log</SectionTitle>
      <Card>
        {events.length === 0 ? <Body muted>Nothing logged yet. Tap "Log care" after you water it.</Body> : null}
        {events.map((event) => (
          <View key={event.event_id} style={styles.event}>
            <View style={{ flex: 1 }}>
              <Text style={styles.eventType}>{event.event_type}</Text>
              {event.notes ? <Text style={styles.eventNotes}>{event.notes}</Text> : null}
            </View>
            <Text style={styles.eventDate}>{shortDate(event.date)}</Text>
          </View>
        ))}
      </Card>
    </Screen>
  );
}

function CareGuide({ care }: { care: Care | null | undefined }) {
  const rows: [string, string | null | undefined][] = [
    ['Water', care?.watering_frequency],
    ['Light', care?.sunlight_requirements?.join(', ')],
    ['Soil', care?.soil_preferences],
    ['Temperature', care?.temperature_range],
    ['Difficulty', care?.difficulty_level],
  ];
  const known = rows.filter(([, value]) => value);
  if (known.length === 0) {
    return <Body muted>We don't have care details for this plant yet.</Body>;
  }
  return (
    <View style={{ gap: space.sm }}>
      {known.map(([label, value]) => (
        <View key={label} style={styles.guideRow}>
          <Text style={styles.guideLabel}>{label}</Text>
          <Text style={styles.guideValue}>{value}</Text>
        </View>
      ))}
    </View>
  );
}

function HealthCard({ record, onChanged }: { record: HealthAssessment; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);

  async function resolve() {
    setBusy(true);
    try {
      await api(`/health/${record.assessment_id}/resolve`, { method: 'POST' });
    } finally {
      setBusy(false);
      onChanged();
    }
  }

  return (
    <Card>
      <View style={styles.healthTop}>
        <View style={{ flex: 1, gap: 4 }}>
          <Text style={styles.eventType}>{record.diagnosis ?? 'Health check'}</Text>
          <Text style={styles.eventDate}>{shortDate(record.assessment_date)}</Text>
        </View>
        <Tag label={record.resolved ? 'Resolved' : 'Ongoing'} tone={record.resolved ? 'green' : 'warm'} />
      </View>
      {record.image_url ? <PlantImage url={record.image_url} style={styles.healthPhoto} label="Photo of the problem" /> : null}
      {record.symptoms.length > 0 ? <Body muted>{record.symptoms.join(' · ')}</Body> : null}
      {record.treatment_recommendations ? <Body>{record.treatment_recommendations}</Body> : null}
      {!record.resolved ? <Button label="Mark as resolved" kind="secondary" small busy={busy} onPress={resolve} /> : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  hero: { width: '100%', aspectRatio: 4 / 3, borderRadius: 22 },
  scientific: { fontSize: 16, fontStyle: 'italic', color: colors.muted },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm, marginTop: space.sm },
  actions: { flexDirection: 'row', gap: space.sm },
  action: { flex: 1, paddingHorizontal: space.sm },
  event: { flexDirection: 'row', gap: space.md, alignItems: 'flex-start' },
  eventType: { fontSize: 16, fontWeight: '600', color: colors.ink },
  eventNotes: { fontSize: 15, color: colors.muted, marginTop: 2 },
  eventDate: { fontSize: 14, color: colors.muted },
  guideRow: { flexDirection: 'row', gap: space.md },
  guideLabel: { width: 104, fontSize: 15, color: colors.muted },
  guideValue: { flex: 1, fontSize: 15, color: colors.ink },
  healthTop: { flexDirection: 'row', alignItems: 'flex-start', gap: space.md },
  healthPhoto: { width: '100%', aspectRatio: 16 / 9, borderRadius: 10 },
});
