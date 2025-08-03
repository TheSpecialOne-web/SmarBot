import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import { Stack } from "@mui/material";
import { ReactNode } from "react";

import { CustomDialog } from "../CustomDialog";
import { CustomDialogAction } from "../CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "../CustomDialog/CustomDialogContent";

const SeverityIcon = {
  error: <ErrorOutlineIcon color="error" fontSize="large" />,
  warning: <WarningAmberOutlinedIcon color="warning" fontSize="large" />,
  info: <InfoOutlinedIcon color="info" fontSize="large" />,
} as const;

type Props = {
  open: boolean;
  onClose: () => void;
  title: string;
  content: ReactNode;
  buttonText: string;
  onSubmit: () => Promise<void> | undefined;
  isLoading: boolean;
  color?: keyof typeof SeverityIcon;
  disabled?: boolean;
};

export const ConfirmDialog = ({
  open,
  onClose,
  title,
  content,
  buttonText,
  onSubmit,
  isLoading,
  color = "error",
  disabled = false,
}: Props) => {
  return (
    <CustomDialog open={open} title={title} onClose={onClose}>
      <CustomDialogContent>
        <Stack
          gap={2}
          alignItems="center"
          sx={{
            py: 3,
            textAlign: "center",
            fontWeight: "bold",
          }}
        >
          {SeverityIcon[color]}
          {content}
        </Stack>
      </CustomDialogContent>
      <CustomDialogAction
        onClose={onClose}
        onSubmit={onSubmit}
        loading={isLoading}
        buttonText={buttonText}
        color={color}
        disabled={disabled}
      />
    </CustomDialog>
  );
};
