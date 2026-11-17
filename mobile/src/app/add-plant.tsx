import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { Body, Button, Card, ErrorNote, Field, PlantImage, Screen, SectionTitle } from '../components/ui';
import { api } from '../lib/api';
import { colors, space } from '../lib/theme';
import type { MyPlant, Plant, TreflePlant } from '../lib/types';

type Result = { plants: Plant[]; more: TreflePlant[] };
type Choice = { key: string; name: string; scientific: string; image: string | null; send: Record<string, number> };

function toChoices(result: Result): Choice[] {
  return [
    ...result.plants.map((p) => ({
      key: `db-${p.plant_id}`,
      name: p.common_name,
      scientific: p.scientific_name,
      image: p.image_url,
      send: { plant_id: p.plant_id },
    })),
    ...result.more.map((p) => ({
      key: `trefle-${p.trefle_id}`,
      name: p.common_name,
      scientific: p.scientific_name,
      image: p.image_url,
      send: { trefle_id: p.trefle_id },
    })),
  ];
}

export default function AddPlant() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [searched, setSearched] = useState<string | null>(null);
  const [choices, setChoices] = useState<Choice[]>([]);
  const [chosen, setChosen] = useState<Choice | null>(null);
  const [nickname, setNickname] = useState('');
  const [location, setLocation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    const text = query.trim();
    if (!text) return;
    setBusy(true);
    setError(null);
    setChosen(null);
    try {
      setChoices(toChoices(await api<Result>(`/plants?search=${encodeURIComponent(text)}`)));
      setSearched(text);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Search failed.');
    } finally {
      setBusy(false);
    }
  }

  async function add() {
    if (!chosen) return;
    setBusy(true);
    setError(null);
    try {
      const { plant } = await api<{ plant: MyPlant }>('/my-plants', {
        body: { ...chosen.send, nickname, location },
      });
      // Replace this screen so Back goes to the list, not back to the search
      router.replace(`/plant/${plant.user_plant_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not add the plant.');
      setBusy(false);
    }
  }

  if (chosen) {
    return (
      <Screen footer={<Button label="Add to my plants" onPress={add} busy={busy} />}>
        <Card style={styles.chosen}>
          <PlantImage url={chosen.image} style={styles.thumbLarge} />
          <View style={{ flex: 1 }}>
            <SectionTitle>{chosen.name}</SectionTitle>
            <Text style={styles.scientific}>{chosen.scientific}</Text>
          </View>
        </Card>
        <ErrorNote message={error} />
        <Field label="Nickname (optional)" placeholder="e.g. Monty" value={nickname} onChangeText={setNickname} maxLength={100} />
        <Field label="Where is it? (optional)" placeholder="e.g. Living room window" value={location} onChangeText={setLocation} maxLength={100} />
        <Button label="Choose a different plant" kind="quiet" onPress={() => setChosen(null)} />
      </Screen>
    );
  }

  return (
    <Screen>
      <Field
        label="What kind of plant is it?"
        placeholder="e.g. monstera, snake plant, basil"
        value={query}
        onChangeText={setQuery}
        autoCorrect={false}
        returnKeyType="search"
        onSubmitEditing={search}
      />
      <Button label="Search" icon="search" onPress={search} busy={busy} disabled={!query.trim()} />
      <ErrorNote message={error} />

      {searched !== null && choices.length === 0 && !busy ? (
        <Body muted>
          Nothing found for "{searched}". Try its other name: the scientific name often works when the everyday one doesn't.
        </Body>
      ) : null}

      {choices.length > 0 ? (
        <Card style={{ padding: 0, gap: 0 }}>
          {choices.map((choice, index) => (
            <Pressable
              key={choice.key}
              accessibilityRole="button"
              accessibilityLabel={`${choice.name}, ${choice.scientific}`}
              onPress={() => setChosen(choice)}
              style={({ pressed }) => [styles.result, index > 0 && styles.divider, pressed && { backgroundColor: colors.sage }]}>
              <PlantImage url={choice.image} style={styles.thumb} />
              <View style={{ flex: 1 }}>
                <Text style={styles.name} numberOfLines={1}>{choice.name}</Text>
                <Text style={styles.scientific} numberOfLines={1}>{choice.scientific}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={colors.muted} />
            </Pressable>
          ))}
        </Card>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  result: { flexDirection: 'row', alignItems: 'center', gap: space.md, padding: space.md, minHeight: 68 },
  divider: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.line },
  thumb: { width: 48, height: 48, borderRadius: 10 },
  thumbLarge: { width: 72, height: 72, borderRadius: 14 },
  chosen: { flexDirection: 'row', alignItems: 'center' },
  name: { fontSize: 16, fontWeight: '600', color: colors.ink },
  scientific: { fontSize: 14, fontStyle: 'italic', color: colors.muted },
});
