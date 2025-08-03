import { MenuItem, Stack, Typography } from "@mui/material";
import { useFormContext } from "react-hook-form";

import { CustomFormSelect } from "./CustomFormSelect";

type MonthPickerProps = {
  disabled: boolean;
};

export const MonthPicker = ({ disabled }: MonthPickerProps) => {
  const { control } = useFormContext<{ month: number }>();

  return (
    <Stack gap={1} direction="row" alignItems="center">
      <CustomFormSelect
        name="month"
        control={control}
        disabled={disabled}
        sx={{
          minWidth: 70,
        }}
      >
        {Array.from({ length: 12 }, (_, i) => (
          <MenuItem key={i} value={i + 1}>
            {i + 1}
          </MenuItem>
        ))}
      </CustomFormSelect>
      <Typography>月</Typography>
    </Stack>
  );
};
