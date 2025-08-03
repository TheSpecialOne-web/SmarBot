import { Box } from "@mui/material";
import { ReactNode } from "react";

type Props = {
  children: ReactNode;
  color: string;
  onClick: () => void;
};

export const SuperscriptLink = ({ children, color, onClick }: Props) => {
  return (
    <Box
      component="sup"
      sx={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 14,
        fontWeight: "500",
        verticalAlign: "top",
        top: -1,
        height: 16,
        minWidth: 16,
        borderRadius: "3px",
        color: color,
        backgroundColor: "citationBackground.main",
        cursor: "pointer",
        textDecoration: "none",
        outline: "transparent solid 1px",
        m: "0 2px",
      }}
      onClick={onClick}
    >
      {children}
    </Box>
  );
};
