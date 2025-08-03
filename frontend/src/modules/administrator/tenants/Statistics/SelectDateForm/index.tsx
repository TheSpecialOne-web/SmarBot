import { Stack } from "@mui/material";

import { MonthPicker } from "@/components/inputs/MonthPicker";
import { YearPicker } from "@/components/inputs/YearPicker";

export type SelectDateFormParams = {
  year: number;
  month: number;
};

type Props = {
  disabled: boolean;
};

export const SelectDateForm = ({ disabled }: Props) => {
  return (
    <Stack gap={1} direction="row" alignItems="center">
      <YearPicker disabled={disabled} />
      <MonthPicker disabled={disabled} />
    </Stack>
  );
};
