// Reminder notifications are created on the phone itself: for every reminder
// the phone schedules a notification at 9 in the morning on its due date.
// Nothing is sent through a notification service, so no server set-up is needed.
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';

import { api } from './api';
import { fromISODate } from './dates';
import type { Reminder } from './types';

const supported = Platform.OS === 'ios' || Platform.OS === 'android';
const REMINDER_HOUR = 9;

if (supported) {
  // Show the notification even when the app is open
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: false,
      shouldSetBadge: false,
    }),
  });
}

export async function notificationsAllowed(): Promise<boolean> {
  if (!supported) return false;
  return (await Notifications.getPermissionsAsync()).granted;
}

/** Shows the system's "Allow notifications?" question if it hasn't been answered yet. */
export async function askForNotifications(): Promise<boolean> {
  if (!supported) return false;
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('reminders', {
      name: 'Plant care reminders',
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }
  const current = await Notifications.getPermissionsAsync();
  if (current.granted) return true;
  if (!current.canAskAgain) return false;
  return (await Notifications.requestPermissionsAsync()).granted;
}

export async function clearReminderNotifications() {
  if (!supported) return;
  try {
    await Notifications.cancelAllScheduledNotificationsAsync();
  } catch {
    // Nothing scheduled
  }
}

/**
 * Makes the phone's scheduled notifications match the reminders on the server.
 * Called whenever reminders may have changed. Never throws.
 */
export async function syncReminderNotifications(reminders?: Reminder[]) {
  if (!supported) return;
  try {
    if (!(await notificationsAllowed())) return;
    const list = reminders ?? (await api<{ reminders: Reminder[] }>('/reminders')).reminders;
    await Notifications.cancelAllScheduledNotificationsAsync();

    const now = Date.now();
    for (const reminder of list) {
      const when = fromISODate(reminder.next_reminder_date);
      when.setHours(REMINDER_HOUR, 0, 0, 0);
      // Already due: it's shown on the Home screen instead of notifying late
      if (when.getTime() <= now) continue;
      await Notifications.scheduleNotificationAsync({
        content: {
          title: `${reminder.reminder_type}: ${reminder.plant_name ?? 'your plant'}`,
          body: `Time for ${reminder.reminder_type.toLowerCase()}. Open Rootly to mark it done.`,
          data: { user_plant_id: reminder.user_plant_id },
        },
        trigger: {
          type: Notifications.SchedulableTriggerInputTypes.DATE,
          date: when,
          channelId: 'reminders',
        },
      });
    }
  } catch {
    // Notifications are a bonus; never let them break a screen
  }
}
