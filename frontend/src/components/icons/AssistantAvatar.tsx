import { Avatar, SxProps } from "@mui/material";
import { RiRobot2Fill } from "react-icons/ri";

import { theme } from "@/theme";

const ICON_SIZE_RATIO = 0.6;

type Props = {
  size?: number;
  iconUrl?: string;
  iconColor: string;
  sx?: SxProps;
  onClick?: () => void;
};

export const AssistantAvatar = ({ size = 30, iconUrl, iconColor, sx, onClick }: Props) => {
  return (
    <Avatar
      src={iconUrl || undefined}
      onClick={onClick}
      alt="icon preview"
      sx={{
        width: size,
        height: size,
        bgcolor: iconUrl ? undefined : iconColor,
        cursor: onClick ? "pointer" : "default",
        boxShadow: "0 0 0 0 transparent",
        transition: "box-shadow 0.2s ease, filter ease",
        ...(onClick && {
          "&:hover": {
            boxShadow: `0 0 0 4px ${theme.palette.boxShadow.main}`,
            filter: "brightness(0.8)",
          },
        }),
        ...sx,
      }}
    >
      <RiRobot2Fill fontSize={size * ICON_SIZE_RATIO} />
    </Avatar>
  );
};
