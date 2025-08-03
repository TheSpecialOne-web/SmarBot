import dayjs from "dayjs";

// 2024年12月1日以降は新料金プラン
export const showOldPricingPlan = (yearMonth: dayjs.Dayjs): boolean => {
  return yearMonth.year() <= 2024 && yearMonth.month() + 1 <= 12;
};
