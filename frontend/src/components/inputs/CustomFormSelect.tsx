import { Box, FormControl, FormHelperText, Select, SelectProps } from "@mui/material";
import React, { ReactNode } from "react";
import { FieldValues, useController, UseControllerProps } from "react-hook-form";

import { CustomLabel } from "../labels/CustomLabel";

type OmitSelectProps = Omit<SelectProps, "size">;

// 'name' と 'control' を必須にする
type RequiredNameAndControlProps<T extends FieldValues> = Required<
  Pick<UseControllerProps<T>, "name" | "control">
> &
  Omit<UseControllerProps<T>, "name" | "control">;

type CustomFormSelectProps<T extends FieldValues> = RequiredNameAndControlProps<T> & {
  label?: string;
  tooltip?: ReactNode;
  children: React.ReactNode; // MenuItem コンポーネントの配列を受け取る
} & OmitSelectProps;

export const CustomFormSelect = <T extends FieldValues>({
  name,
  label,
  control,
  rules,
  tooltip,
  children, // MenuItem コンポーネントの配列
  ...props
}: CustomFormSelectProps<T>) => {
  const {
    field,
    fieldState: { error },
  } = useController<T>({ name, control, rules });

  return (
    <Box>
      {label && <CustomLabel label={label} tooltip={tooltip} required={Boolean(rules?.required)} />}
      <FormControl
        fullWidth
        error={Boolean(error)}
        sx={{
          mt: 0,
        }}
      >
        <Select {...field} {...props} fullWidth size="small">
          {children}
        </Select>
        {error && <FormHelperText>{error?.message}</FormHelperText>}
      </FormControl>
    </Box>
  );
};
