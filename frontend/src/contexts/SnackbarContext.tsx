import { styled } from "@mui/material";
import { MaterialDesignContent, SnackbarProvider } from "notistack";
import { ReactNode } from "react";

const StyledMaterialDesignContent = styled(MaterialDesignContent)(() => ({
  "&.notistack-MuiContent-default": {
    color: "inherit",
    backgroundColor: "white",
  },
}));

type Props = {
  children: ReactNode;
};

export const CustomSnackbarProvider = ({ children }: Props) => {
  return (
    <SnackbarProvider
      autoHideDuration={5000}
      maxSnack={2}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      Components={{
        default: StyledMaterialDesignContent,
      }}
    >
      {children}
    </SnackbarProvider>
  );
};
