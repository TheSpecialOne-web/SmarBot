import { Box, SxProps, TextFieldProps } from "@mui/material";
import { TimePicker } from "@mui/x-date-pickers/TimePicker";
import { FieldValues, useController, UseControllerProps } from "react-hook-form";

import { CustomLabel } from "../labels/CustomLabel";

type OmitTextFieldProps = Omit<TextFieldProps, "error" | "helperText" | "size">;

type RequiredNameAndControlProps<T extends FieldValues> = Required<
  Pick<UseControllerProps<T>, "name" | "control">
> &
  Omit<UseControllerProps<T>, "name" | "control">;

type TimePickerComponentProps<T extends FieldValues> = RequiredNameAndControlProps<T> & {
  label?: string;
  tooltip?: string;
  boxSx?: SxProps;
} & OmitTextFieldProps;

export const CustomTimePicker = <T extends FieldValues>({
  name,
  label,
  control,
  rules,
  tooltip,
  boxSx,
  ...props
}: TimePickerComponentProps<T>) => {
  const { field, fieldState } = useController<T>({ name, control, rules });
  const { error } = fieldState;

  return (
    <Box sx={boxSx}>
      {label && <CustomLabel label={label} tooltip={tooltip} required={Boolean(rules?.required)} />}

      <TimePicker
        value={field.value}
        onChange={newValue => {
          field.onChange(newValue);
        }}
        slotProps={{
          textField: {
            size: "small",
            error: Boolean(error),
            helperText: error?.message,
            ...props,
          },
        }}
      />
    </Box>
  );
};
