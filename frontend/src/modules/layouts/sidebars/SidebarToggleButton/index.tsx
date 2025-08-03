import CloseIcon from "@mui/icons-material/Close";
import ShortTextIcon from "@mui/icons-material/ShortText";
import { IconButton } from "@mui/material";

import { CHAT_LAYOUT_SIDEBAR_WIDTH } from "@/const";

type Props = {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
};

export const SidebarToggleButton = ({ isSidebarOpen, toggleSidebar }: Props) => {
  return (
    <IconButton
      onClick={toggleSidebar}
      sx={{
        position: "absolute",
        top: "20px",
        left: isSidebarOpen ? `calc(${CHAT_LAYOUT_SIDEBAR_WIDTH}px + 4px)` : "4px",
        transform: "translateY(-50%)",
        p: 0,
        width: "fit-content",
        height: "fit-content",
        zIndex: 999,
      }}
    >
      {isSidebarOpen ? <CloseIcon /> : <ShortTextIcon />}
    </IconButton>
  );
};
