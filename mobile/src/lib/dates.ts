// Reminder dates travel as "YYYY-MM-DD" and mean a day on the phone's own calendar.

export function toISODate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

export function fromISODate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
}

export function todayISO(): string {
  return toISODate(new Date());
}

export function addDays(days: number, from: Date = new Date()): Date {
  const result = new Date(from.getFullYear(), from.getMonth(), from.getDate());
  result.setDate(result.getDate() + days);
  return result;
}

/** Whole days from today until the date (negative when it has passed). */
export function daysUntil(value: string): number {
  const today = addDays(0);
  return Math.round((fromISODate(value).getTime() - today.getTime()) / 86400000);
}

export function dueLabel(value: string): string {
  const days = daysUntil(value);
  if (days < -1) return `${-days} days overdue`;
  if (days === -1) return 'Due yesterday';
  if (days === 0) return 'Due today';
  if (days === 1) return 'Tomorrow';
  if (days < 7) return `In ${days} days`;
  return fromISODate(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

/** "Mar 3" for a time the server sent (UTC, ending in Z). */
export function shortDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}
