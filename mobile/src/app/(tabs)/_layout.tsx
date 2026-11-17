import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { colors, serif } from '../../lib/theme';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: colors.cream },
        headerTitleStyle: { fontFamily: serif, color: colors.forest },
        headerShadowVisible: false,
        tabBarActiveTintColor: colors.forest,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: { backgroundColor: colors.paper, borderTopColor: colors.line },
        sceneStyle: { backgroundColor: colors.cream },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Today',
          tabBarIcon: ({ focused, size }) => <Ionicons name="sunny-outline" color={focused ? colors.forest : colors.muted} size={size} />,
        }}
      />
      <Tabs.Screen
        name="plants"
        options={{
          title: 'My plants',
          tabBarIcon: ({ focused, size }) => <Ionicons name="leaf-outline" color={focused ? colors.forest : colors.muted} size={size} />,
        }}
      />
      <Tabs.Screen
        name="account"
        options={{
          title: 'Account',
          tabBarIcon: ({ focused, size }) => <Ionicons name="person-outline" color={focused ? colors.forest : colors.muted} size={size} />,
        }}
      />
    </Tabs>
  );
}
