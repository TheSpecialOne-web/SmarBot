import { Paper } from "@mui/material";
import { ReactNode } from "react";

type Props = {
  children: ReactNode;
};

export const ContentHeader = ({ children }: Props) => {
  return (
    <Paper
      sx={{
        backgroundColor: "tableBackground.main",
        padding: 2,
        borderRadius: "4px 4px 0 0",
        marginBottom: "-1px",
        borderBottom: "none",
      }}
      variant="outlined"
    >
      {children}
    </Paper>
  );
};
