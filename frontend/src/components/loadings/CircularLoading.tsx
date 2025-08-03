import { Box, CircularProgress, SxProps } from "@mui/material";

type Props = {
  size?: number;
  sx?: SxProps;
};

export const CircularLoading = ({
  size = 48,
  sx = {
    py: 5,
  },
}: Props) => {
  return (
    <Box display="flex" justifyContent="center" sx={sx}>
      <CircularProgress size={size} />
    </Box>
  );
};
