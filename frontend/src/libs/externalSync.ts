export const DayOfWeek = {
  Sunday: "sun",
  Monday: "mon",
  Tuesday: "tue",
  Wednesday: "wed",
  Thursday: "thu",
  Friday: "fri",
  Saturday: "sat",
} as const;

export type DayOfWeek = (typeof DayOfWeek)[keyof typeof DayOfWeek];

export const dayOfWeekLabels = {
  [DayOfWeek.Sunday]: "日曜日",
  [DayOfWeek.Monday]: "月曜日",
  [DayOfWeek.Tuesday]: "火曜日",
  [DayOfWeek.Wednesday]: "水曜日",
  [DayOfWeek.Thursday]: "木曜日",
  [DayOfWeek.Friday]: "金曜日",
  [DayOfWeek.Saturday]: "土曜日",
};

export type SyncSchedule = {
  syncFrequencyWeek: number;
  syncDay: DayOfWeek;
  syncHour: number;
};

export const scheduleToCron = ({ syncFrequencyWeek, syncDay, syncHour }: SyncSchedule) => {
  const syncFrequencyDay = syncFrequencyWeek * 7;
  return `0 ${syncHour} */${syncFrequencyDay} * ${syncDay}`;
};
