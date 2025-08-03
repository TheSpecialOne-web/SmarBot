import { HelpOutline } from "@mui/icons-material";
import { Checkbox, FormControlLabel, Stack, Tooltip } from "@mui/material";
import { ChangeEvent, ReactNode } from "react";
import {
  Controller,
  ControllerRenderProps,
  FieldValues,
  Path,
  UseControllerProps,
} from "react-hook-form";

import { IconButtonWithTooltip } from "../buttons/IconButtonWithTooltip";

type CustomFormCheckboxProps<T extends FieldValues> = {
  disabled?: boolean;
  label: string;
  checked?: (field: ControllerRenderProps<T, Path<T>>) => boolean;
  onChange?: (
    event: ChangeEvent<HTMLInputElement>,
    field: ControllerRenderProps<T, Path<T>>,
  ) => void;
  disabledTooltipTitle?: ReactNode; // disabledの場合のtooltip
  tooltipTitle?: ReactNode;
} & UseControllerProps<T>;

export const CustomFormCheckbox = <T extends FieldValues>({
  name,
  control,
  defaultValue,
  disabled,
  label,
  checked,
  onChange,
  disabledTooltipTitle,
  tooltipTitle,
  ...props
}: CustomFormCheckboxProps<T>) => {
  return (
    <Controller
      name={name}
      control={control}
      defaultValue={defaultValue}
      render={({ field }) => (
        <Tooltip title={disabled && disabledTooltipTitle} placement="top-start" arrow>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ width: "fit-content" }}>
            <FormControlLabel
              disabled={disabled}
              control={
                <Checkbox
                  {...props}
                  {...field}
                  name={name}
                  checked={checked ? checked(field) : field.value}
                  onChange={e => {
                    onChange ? onChange(e, field) : field.onChange(e.target.checked);
                  }}
                  sx={{ p: 0, mr: 1 }}
                />
              }
              label={label}
              sx={{ mx: 0 }}
            />
            {tooltipTitle && !disabled && (
              <IconButtonWithTooltip
                tooltipTitle={tooltipTitle}
                color="primary"
                icon={<HelpOutline sx={{ fontSize: 18 }} />}
                iconButtonSx={{ p: 0 }}
              />
            )}
          </Stack>
        </Tooltip>
      )}
    />
  );
};
