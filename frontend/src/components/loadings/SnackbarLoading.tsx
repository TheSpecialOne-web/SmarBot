import { CircularProgress, Stack, Typography } from "@mui/material";

type Props = {
  message: string;
};

export const SnackbarLoading = ({ message }: Props) => {
  return (
    <Stack direction="row" gap={1} alignItems="center">
      <CircularProgress size={20} />
      <Typography variant="body2">{message}</Typography>
    </Stack>
  );
};
