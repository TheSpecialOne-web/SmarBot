import { CircularProgress, Dialog, Stack, Typography } from "@mui/material";

type Props = {
  open: boolean;
};

export const LoadingDialog = ({ open }: Props) => {
  return (
    <Dialog open={open}>
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="center"
        gap={2}
        sx={{
          p: 3,
        }}
      >
        <CircularProgress size={24} />
        <Typography>読み込み中です</Typography>
      </Stack>
    </Dialog>
  );
};
