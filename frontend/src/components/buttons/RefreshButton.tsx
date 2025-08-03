import RefreshIcon from "@mui/icons-material/Refresh";
import { Button } from "@mui/material";

type Props = {
  onClick: () => void;
};

export const RefreshButton = ({ onClick }: Props) => (
  <Button onClick={onClick} color="inherit" variant="outlined">
    <RefreshIcon />
  </Button>
);
