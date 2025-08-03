import RefreshIcon from "@mui/icons-material/Refresh";
import { Button, Typography } from "@mui/material";

type Props = {
  onClick: () => void;
  disabled?: boolean;
};

export const InitializeChatButton = ({ disabled, onClick }: Props) => {
  return (
    <Button startIcon={<RefreshIcon />} onClick={onClick} disabled={disabled} variant="text">
      <Typography variant="subtitle2">新しいチャットを始める</Typography>
    </Button>
  );
};
