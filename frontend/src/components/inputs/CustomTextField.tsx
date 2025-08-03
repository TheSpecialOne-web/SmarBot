import { Box, SxProps, TextField, TextFieldProps } from "@mui/material";
import { FieldValues, useController, UseControllerProps } from "react-hook-form";

import { CustomLabel } from "../labels/CustomLabel";

type OmitTextFieldProps = Omit<TextFieldProps, "error" | "helperText" | "size">;

// 'name' と 'control' を必須にする
type RequiredNameAndControlProps<T extends FieldValues> = Required<
  Pick<UseControllerProps<T>, "name" | "control">
> &
  Omit<UseControllerProps<T>, "name" | "control">;

type InputItemComponentProps<T extends FieldValues> = RequiredNameAndControlProps<T> & {
  label?: string;
  tooltip?: string;
  boxSx?: SxProps;
} & OmitTextFieldProps;

export const CustomTextField = <T extends FieldValues>({
  name,
  label,
  control,
  rules,
  tooltip,
  boxSx,
  ...props
}: InputItemComponentProps<T>) => {
  const { field, fieldState } = useController<T>({ name, control, rules });

  const { error } = fieldState;

  return (
    <Box sx={boxSx}>
      {label && <CustomLabel label={label} tooltip={tooltip} required={Boolean(rules?.required)} />}

      <TextField
        {...field}
        sx={{ mt: 0 }}
        {...props}
        size="small"
        error={Boolean(error)}
        helperText={error?.message}
      />
    </Box>
  );
};
