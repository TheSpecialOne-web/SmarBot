import { Grid, Typography } from "@mui/material";
import { ReactNode } from "react";

export type Props = {
  title: string;
  content: ReactNode;
};

export const BasicInfoItem = ({ title, content }: Props) => {
  return (
    <Grid item xs={12} sm={6}>
      <Typography variant="h5">{title}</Typography>
      <Typography pl={1}>{content}</Typography>
    </Grid>
  );
};
