import { Typography } from "@mui/material";

type Props = {
  text: string;
};

export const SubtitleText = ({ text }: Props) => {
  return (
    <Typography variant="subtitle2" fontSize={12} color="secondary" pl={1} mb={0.5}>
      {text}
    </Typography>
  );
};
