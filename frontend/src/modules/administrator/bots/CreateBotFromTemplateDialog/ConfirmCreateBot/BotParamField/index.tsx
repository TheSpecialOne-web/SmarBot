import { Box, Typography } from "@mui/material";

import { CustomLabel } from "@/components/labels/CustomLabel";

type Props = {
  title: string;
  value: string;
};

export const BotParamField = ({ title, value }: Props) => {
  return (
    <Box>
      <CustomLabel label={title} />
      <Typography variant="subtitle1">{value}</Typography>
    </Box>
  );
};
