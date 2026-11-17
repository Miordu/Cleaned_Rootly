// The small building blocks every screen is made from.
import { type ReactNode } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type StyleProp,
  type TextInputProps,
  type ViewStyle,
} from 'react-native';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';

import { imageUrl } from '../lib/api';
import { colors, radius, serif, space } from '../lib/theme';

export function Screen({
  children,
  onRefresh,
  refreshing = false,
  footer,
}: {
  children: ReactNode;
  onRefresh?: () => void;
  refreshing?: boolean;
  /** Stays at the bottom of the screen (for a main button) */
  footer?: ReactNode;
}) {
  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}>
      <ScrollView
        style={styles.flex}
        contentContainerStyle={styles.screen}
        keyboardShouldPersistTaps="handled"
        refreshControl={
          onRefresh ? (
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.leaf} />
          ) : undefined
        }>
        <View style={styles.column}>{children}</View>
      </ScrollView>
      {footer ? <View style={styles.footer}>{footer}</View> : null}
    </KeyboardAvoidingView>
  );
}

export function Title({ children }: { children: ReactNode }) {
  return (
    <Text accessibilityRole="header" style={styles.title}>
      {children}
    </Text>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <Text accessibilityRole="header" style={styles.sectionTitle}>
      {children}
    </Text>
  );
}

export function Body({ children, muted, style }: { children: ReactNode; muted?: boolean; style?: StyleProp<any> }) {
  return <Text style={[styles.body, muted && { color: colors.muted }, style]}>{children}</Text>;
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

type ButtonProps = {
  label: string;
  onPress: () => void;
  kind?: 'primary' | 'secondary' | 'danger' | 'quiet';
  busy?: boolean;
  disabled?: boolean;
  icon?: keyof typeof Ionicons.glyphMap;
  small?: boolean;
  style?: StyleProp<ViewStyle>;
};

export function Button({ label, onPress, kind = 'primary', busy, disabled, icon, small, style }: ButtonProps) {
  const text =
    kind === 'primary' ? colors.white : kind === 'danger' ? colors.terracotta : colors.forest;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || busy, busy }}
      disabled={disabled || busy}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        small && styles.buttonSmall,
        kind === 'primary' && { backgroundColor: colors.forest },
        kind === 'secondary' && { backgroundColor: colors.sage },
        kind === 'danger' && { backgroundColor: colors.terracottaSoft },
        (disabled || busy) && { opacity: 0.55 },
        pressed && { opacity: 0.8 },
        style,
      ]}>
      {busy ? (
        <ActivityIndicator color={text} />
      ) : (
        <>
          {icon ? <Ionicons name={icon} size={small ? 16 : 19} color={text} /> : null}
          <Text style={[styles.buttonText, small && { fontSize: 14 }, { color: text }]}>{label}</Text>
        </>
      )}
    </Pressable>
  );
}

export function Field({ label, hint, ...input }: { label: string; hint?: string } & TextInputProps) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor="#9AA39A"
        {...input}
        style={[styles.input, input.multiline && styles.inputMultiline, input.style]}
      />
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

/** A row of choices where one (or, with `multiple`, several) can be picked. */
export function Choices({
  label,
  options,
  selected,
  onToggle,
}: {
  label?: string;
  options: string[];
  selected: string[];
  onToggle: (option: string) => void;
}) {
  return (
    <View style={styles.field}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <View style={styles.chips}>
        {options.map((option) => {
          const on = selected.includes(option);
          return (
            <Pressable
              key={option}
              accessibilityRole="button"
              accessibilityState={{ selected: on }}
              onPress={() => onToggle(option)}
              style={[styles.chip, on && styles.chipOn]}>
              <Text style={[styles.chipText, on && { color: colors.white }]}>{option}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <View style={styles.error} accessibilityRole="alert">
      <Ionicons name="alert-circle" size={18} color={colors.terracotta} />
      <Text style={styles.errorText}>{message}</Text>
    </View>
  );
}

export function Loading() {
  return (
    <View style={styles.centered}>
      <ActivityIndicator color={colors.leaf} size="large" />
    </View>
  );
}

export function LoadProblem({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={styles.centered}>
      <Ionicons name="cloud-offline-outline" size={36} color={colors.muted} />
      <Body muted style={{ textAlign: 'center' }}>
        {message}
      </Body>
      <Button label="Try again" kind="secondary" onPress={onRetry} />
    </View>
  );
}

export function Empty({
  icon,
  title,
  text,
  children,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  text: string;
  children?: ReactNode;
}) {
  return (
    <Card style={styles.empty}>
      <Ionicons name={icon} size={34} color={colors.leaf} />
      <Text style={styles.emptyTitle}>{title}</Text>
      <Body muted style={{ textAlign: 'center' }}>
        {text}
      </Body>
      {children}
    </Card>
  );
}

/** A plant photo, or a leaf on a soft green background when there isn't one. */
export function PlantImage({
  url,
  style,
  label,
}: {
  url: string | null | undefined;
  style?: StyleProp<any>;
  label?: string;
}) {
  const source = imageUrl(url);
  if (!source) {
    return (
      <View style={[styles.imagePlaceholder, style]} accessibilityLabel={label ?? 'No photo yet'}>
        <Ionicons name="leaf-outline" size={30} color={colors.leaf} />
      </View>
    );
  }
  return (
    <Image
      source={{ uri: source }}
      style={[{ backgroundColor: colors.sage }, style]}
      contentFit="cover"
      transition={150}
      accessibilityLabel={label}
    />
  );
}

export function Tag({ label, tone = 'green' }: { label: string; tone?: 'green' | 'warm' }) {
  return (
    <View style={[styles.tag, tone === 'warm' && { backgroundColor: colors.terracottaSoft }]}>
      <Text style={[styles.tagText, tone === 'warm' && { color: colors.terracotta }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.cream },
  screen: { padding: space.lg, paddingBottom: space.xxl, alignItems: 'center' },
  // Keeps lines a comfortable length on tablets and in a browser
  column: { width: '100%', maxWidth: 560, gap: space.lg },
  footer: {
    padding: space.lg,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.line,
    backgroundColor: colors.cream,
  },
  title: { fontFamily: serif, fontSize: 30, lineHeight: 36, color: colors.forest },
  sectionTitle: { fontFamily: serif, fontSize: 20, color: colors.forest },
  body: { fontSize: 16, lineHeight: 23, color: colors.ink },
  card: {
    backgroundColor: colors.paper,
    borderRadius: radius.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.line,
    padding: space.lg,
    gap: space.md,
  },
  button: {
    minHeight: 50,
    borderRadius: radius.md,
    paddingHorizontal: space.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.sm,
  },
  buttonSmall: { minHeight: 44, paddingHorizontal: space.md, borderRadius: radius.sm },
  buttonText: { fontSize: 16, fontWeight: '600' },
  field: { gap: 6 },
  label: { fontSize: 14, fontWeight: '600', color: colors.forest },
  hint: { fontSize: 13, color: colors.muted },
  input: {
    minHeight: 48,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.white,
    paddingHorizontal: space.md,
    paddingVertical: 10,
    fontSize: 16,
    color: colors.ink,
  },
  inputMultiline: { minHeight: 96, textAlignVertical: 'top' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  chip: {
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: space.lg,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.white,
  },
  chipOn: { backgroundColor: colors.leaf, borderColor: colors.leaf },
  chipText: { fontSize: 15, color: colors.ink },
  error: {
    flexDirection: 'row',
    gap: space.sm,
    alignItems: 'center',
    backgroundColor: colors.terracottaSoft,
    borderRadius: radius.sm,
    padding: space.md,
  },
  errorText: { flex: 1, color: colors.terracotta, fontSize: 15 },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.lg,
    padding: space.xl,
    backgroundColor: colors.cream,
  },
  empty: { alignItems: 'center', paddingVertical: space.xl },
  emptyTitle: { fontFamily: serif, fontSize: 20, color: colors.forest, textAlign: 'center' },
  imagePlaceholder: { backgroundColor: colors.sage, alignItems: 'center', justifyContent: 'center' },
  tag: {
    alignSelf: 'flex-start',
    backgroundColor: colors.sage,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  tagText: { fontSize: 13, fontWeight: '600', color: colors.forest },
});
