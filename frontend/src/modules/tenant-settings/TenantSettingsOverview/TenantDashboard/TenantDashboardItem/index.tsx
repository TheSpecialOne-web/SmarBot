import { Skeleton, Stack, Typography } from "@mui/material";
import { ReactNode } from "react";

type Props = {
  title: string;
  isLoading: boolean;
  children: ReactNode;
};

export const TenantDashboardItem = ({ title, isLoading, children }: Props) => {
  return (
    <Stack alignItems="center" justifyContent="center">
      <Typography variant="h5" gutterBottom>
        {title}
      </Typography>
      {isLoading ? (
        <Skeleton animation="pulse" variant="text" width={24} height={32} />
      ) : (
        <>{children}</>
      )}
    </Stack>
  );
};
