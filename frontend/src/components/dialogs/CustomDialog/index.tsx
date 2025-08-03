import { Dialog, DialogProps, DialogTitle, Stack } from "@mui/material";
import { ReactNode } from "react";

type Props = {
  open: boolean;
  onClose?: () => void;
  title: ReactNode;
  maxWidth?: DialogProps["maxWidth"];
  minHeight?: number;
  children: ReactNode;
  titleActions?: ReactNode;
  disableBackdropClick?: boolean;
};

export const CustomDialog = ({
  open,
  onClose,
  title,
  maxWidth = "sm",
  minHeight,
  children,
  titleActions,
  disableBackdropClick,
}: Props) => {
  const handleClose = (_: object, reason: "backdropClick" | "escapeKeyDown") => {
    if (disableBackdropClick && reason === "backdropClick") return;
    if (onClose) onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth={maxWidth}
      sx={{
        "& .MuiDialog-paper": {
          minHeight: minHeight,
        },
      }}
    >
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          {title}
          {titleActions}
        </Stack>
      </DialogTitle>
      {children}
    </Dialog>
  );
};
