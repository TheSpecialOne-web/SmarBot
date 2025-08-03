import { Fab, SxProps, Tooltip } from "@mui/material";
import { ReactNode } from "react";

import { theme } from "@/theme";

type Props = {
  onClick: () => void;
  icon: ReactNode;
  tooltipTitle: string | ReactNode;
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
  fabSx?: SxProps;
};

export const FloatIconButton = ({
  onClick,
  icon,
  tooltipTitle,
  placement = "top",
  fabSx,
}: Props) => {
  return (
    <Tooltip title={tooltipTitle} placement={placement} arrow>
      <Fab
        sx={{
          backgroundColor: "white",
          borderRadius: "12px",
          width: "34px",
          height: "34px",
          boxShadow: `0px 2px 4px ${theme.palette.boxShadow.main}`,
          color: "success",
          ...fabSx,
        }}
        onClick={onClick}
      >
        {icon}
      </Fab>
    </Tooltip>
  );
};
