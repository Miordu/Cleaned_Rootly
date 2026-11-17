import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { Button, Empty, LoadProblem, Loading, PlantImage, Screen, Tag } from '../../components/ui';
import { api } from '../../lib/api';
import { colors, radius, space } from '../../lib/theme';
import { useLoad } from '../../lib/useLoad';
import type { MyPlant } from '../../lib/types';

export default function Plants() {
  const router = useRouter();
  const { data, error, loading, refreshing, reload } = useLoad(
    async () => (await api<{ plants: MyPlant[] }>('/my-plants')).plants,
  );

  if (loading) return <Loading />;
  if (!data) return <LoadProblem message={error ?? ''} onRetry={() => reload(true)} />;

  return (
    <Screen
      onRefresh={() => reload(true)}
      refreshing={refreshing}
      footer={<Button label="Add a plant" icon="add" onPress={() => router.push('/add-plant')} />}>
      {data.length === 0 ? (
        <Empty icon="leaf-outline" title="Your collection is empty" text="Add the plants you own to keep track of their care." />
      ) : (
        <View style={styles.grid}>
          {data.map((plant) => (
            <Pressable
              key={plant.user_plant_id}
              style={({ pressed }) => [styles.tile, pressed && { opacity: 0.85 }]}
              accessibilityRole="button"
              accessibilityLabel={plant.name}
              onPress={() => router.push(`/plant/${plant.user_plant_id}`)}>
              <PlantImage url={plant.image_url} style={styles.photo} />
              <View style={styles.tileText}>
                <Text style={styles.name} numberOfLines={1}>
                  {plant.name}
                </Text>
                <Text style={styles.place} numberOfLines={1}>
                  {plant.location ?? plant.plant.scientific_name}
                </Text>
                {plant.status && plant.status !== 'active' ? <Tag label={plant.status} tone="warm" /> : null}
              </View>
            </Pressable>
          ))}
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: space.md },
  tile: {
    // Two across, and a single plant doesn't stretch to fill the row
    flexBasis: '47%',
    flexGrow: 0,
    backgroundColor: colors.paper,
    borderRadius: radius.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.line,
    overflow: 'hidden',
  },
  photo: { width: '100%', aspectRatio: 1 },
  tileText: { padding: space.md, gap: 4 },
  name: { fontSize: 16, fontWeight: '600', color: colors.ink },
  place: { fontSize: 14, color: colors.muted },
});
