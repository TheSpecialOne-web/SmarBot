import HubSharpIcon from "@mui/icons-material/HubSharp";
import { Avatar, SxProps } from "@mui/material";

const ICON_SIZE_RATIO = 0.6;

type Props = {
  size?: number;
  sx?: SxProps;
  bgColor: string;
};

export const BasicAiAvater = ({ size = 30, sx, bgColor }: Props) => {
  return (
    <Avatar
      alt="icon preview"
      variant="rounded"
      sx={{
        width: size,
        height: size,
        bgcolor: bgColor,
        boxShadow: "0 0 0 0 transparent",
        transition: "box-shadow 0.2s ease, filter ease",
        ...sx,
      }}
    >
      <HubSharpIcon style={{ fontSize: size * ICON_SIZE_RATIO }} />
    </Avatar>
  );
};
