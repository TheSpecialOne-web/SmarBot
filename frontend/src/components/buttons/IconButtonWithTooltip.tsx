import { Box, IconButton, IconButtonProps, SxProps, Tooltip, Typography } from "@mui/material";
import { ReactNode } from "react";

type Props = {
  onClick?: IconButtonProps["onClick"];
  tooltipTitle?: string | ReactNode;
  placement?:
    | "top-start"
    | "top"
    | "top-end"
    | "right-start"
    | "right"
    | "right-end"
    | "bottom-start"
    | "bottom"
    | "bottom-end"
    | "left-start"
    | "left"
    | "left-end";
  color?: "inherit" | "primary" | "secondary" | "success" | "error" | "info" | "warning";
  disabled?: boolean;
  icon: ReactNode;
  iconButtonSx?: SxProps;
  arrow?: boolean;
  offset?: number;
};

export const IconButtonWithTooltip = ({
  onClick,
  color,
  tooltipTitle,
  placement = "top",
  disabled,
  icon,
  iconButtonSx,
  arrow = true,
  offset = 0,
}: Props) => {
  return (
    <Tooltip
      title={tooltipTitle && <Typography variant="body2">{tooltipTitle}</Typography>}
      placement={placement}
      arrow={arrow}
      slotProps={{
        popper: {
          modifiers: [
            {
              name: "offset",
              options: {
                offset: [0, offset],
              },
            },
          ],
        },
      }}
    >
      <Box width="fit-content">
        <IconButton onClick={onClick} disabled={disabled} color={color} sx={iconButtonSx}>
          {icon}
        </IconButton>
      </Box>
    </Tooltip>
  );
};
