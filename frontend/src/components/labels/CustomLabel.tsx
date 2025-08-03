import { HelpOutline } from "@mui/icons-material";
import { InputLabel, Stack, Typography } from "@mui/material";
import { ReactNode } from "react";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";

type Props = {
  label?: string;
  tooltip?: ReactNode;
  required?: boolean;
};

export const CustomLabel = ({ label, tooltip, required = false }: Props) => {
  return (
    <Stack direction="row" alignItems="center" gap={0.5}>
      <InputLabel
        shrink
        sx={{
          transform: "none",
          "& .MuiInputLabel-asterisk": {
            color: "red",
            fontSize: 14,
          },
        }}
        required={required}
      >
        <Typography component="span" variant="body2">
          {label}
        </Typography>
      </InputLabel>
      {tooltip && (
        <IconButtonWithTooltip
          tooltipTitle={tooltip}
          color="primary"
          icon={
            <HelpOutline
              sx={{
                fontSize: 18,
              }}
            />
          }
          iconButtonSx={{
            padding: 0,
          }}
          placement="top-start"
        />
      )}
    </Stack>
  );
};
