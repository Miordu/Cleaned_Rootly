import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { Loading } from '../components/ui';
import { AuthProvider, useAuth } from '../lib/auth';
import { colors, serif } from '../lib/theme';

function Screens() {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.cream },
        headerTintColor: colors.forest,
        headerTitleStyle: { fontFamily: serif },
        headerShadowVisible: false,
        headerBackButtonDisplayMode: 'minimal',
        contentStyle: { backgroundColor: colors.cream },
      }}>
      {/* Only reachable when logged in */}
      <Stack.Protected guard={user !== null}>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="add-plant" options={{ title: 'Add a plant' }} />
        <Stack.Screen name="plant/[id]/index" options={{ title: '' }} />
        <Stack.Screen name="plant/[id]/edit" options={{ title: 'Edit plant' }} />
        <Stack.Screen name="plant/[id]/care" options={{ title: 'Log care', presentation: 'modal' }} />
        <Stack.Screen name="plant/[id]/reminder" options={{ title: 'New reminder', presentation: 'modal' }} />
        <Stack.Screen name="plant/[id]/health" options={{ title: 'Health check', presentation: 'modal' }} />
      </Stack.Protected>

      {/* Only reachable when logged out */}
      <Stack.Protected guard={user === null}>
        <Stack.Screen name="login" options={{ headerShown: false }} />
        <Stack.Screen name="register" options={{ title: 'Create account' }} />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <StatusBar style="dark" />
      <Screens />
    </AuthProvider>
  );
}
