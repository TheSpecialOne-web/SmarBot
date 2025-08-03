import { MenuItem, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";
import { useFormContext } from "react-hook-form";

import { FIRST_YEAR } from "@/const";

import { CustomFormSelect } from "./CustomFormSelect";

type YearPickerProps = {
  disabled: boolean;
};

export const YearPicker = ({ disabled }: YearPickerProps) => {
  const currentYear = dayjs().year();
  const { control } = useFormContext<{ year: number }>();

  return (
    <Stack gap={1} direction="row" alignItems="center">
      <CustomFormSelect
        name="year"
        control={control}
        disabled={disabled}
        sx={{
          minWidth: 90,
        }}
      >
        {Array.from({ length: currentYear - FIRST_YEAR + 1 }, (_, i) => (
          <MenuItem key={i} value={currentYear - i}>
            {currentYear - i}
          </MenuItem>
        ))}
      </CustomFormSelect>
      <Typography>年</Typography>
    </Stack>
  );
};
