import { Box } from "@mui/material";
import { ReactNode } from "react";

type Props = {
  bgcolor?: string;
  height?: number;
  children: ReactNode;
};

export const HeaderContainer = ({ bgcolor = "background.paper", height, children }: Props) => {
  return (
    <Box
      component="header"
      role="banner"
      sx={{
        alignItems: "center",
        justifyContent: "space-between",
        px: 2,
        py: 1,
        display: "flex",
        borderBottom: 1,
        borderColor: "grey.300",
        bgcolor: bgcolor,
        width: "100%",
        height: height,
        position: "fixed",
        boxShadow: "border-box",
        zIndex: 1100,
      }}
    >
      {children}
    </Box>
  );
};
