import { Box, Drawer } from "@mui/material";
import { useState } from "react";

import { DocumentDisplay } from "@/modules/chat/DocumentDisplay";
import { DocumentToDisplay } from "@/types/document";

type Props = {
  open: boolean;
  onClose: () => void;
  documentToDisplay: DocumentToDisplay | null;
  isLoading: boolean;
  readPdfError: boolean;
};

export const DataConsolePanel = ({
  open,
  onClose,
  documentToDisplay,
  isLoading,
  readPdfError,
}: Props) => {
  const [drawerWidth, setDrawerWidth] = useState<number>(window.innerWidth * 0.4);
  const [isMouseDown, setIsMouseDown] = useState<boolean>(false);

  const handleResize = (e: MouseEvent) => {
    setDrawerWidth(window.innerWidth - e.clientX);
  };

  const handleMouseDown = () => {
    setIsMouseDown(true);
    window.addEventListener("mousemove", handleResize);
    window.addEventListener("mouseup", handleMouseUp);
  };

  const handleMouseUp = () => {
    setIsMouseDown(false);
    window.removeEventListener("mousemove", handleResize);
    window.removeEventListener("mouseup", handleMouseUp);
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
        },
      }}
    >
      <DocumentDisplay
        loading={isLoading}
        error={readPdfError}
        documentToDisplay={documentToDisplay}
      />

      <Box
        sx={{
          position: "absolute",
          top: 0,
          right: 0,
          width: drawerWidth,
          height: "100%",
          zIndex: 9999,
          bgcolor: "transparent",
          visibility: open && isMouseDown ? "visible" : "hidden",
        }}
      >
        <Box
          sx={{
            cursor: "ew-resize",
            position: "absolute",
            top: 0,
            left: 0,
            width: 4,
            height: "100%",
            zIndex: 9999,
            bgcolor: "drawerBackground.main",
            visibility: open ? "visible" : "hidden",
          }}
          onMouseDown={handleMouseDown}
        />
      </Box>
    </Drawer>
  );
};
