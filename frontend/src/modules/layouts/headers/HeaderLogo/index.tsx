import { Divider, Stack, Typography } from "@mui/material";
import { ReactNode } from "react";

type Props = {
  logoUrl: string;
  name: ReactNode;
};

export const HeaderLogo = ({ logoUrl, name }: Props) => {
  return (
    <Stack direction="row" alignItems="center" gap={1}>
      <Stack justifyContent="center" alignItems="center">
        <img src={logoUrl} alt="Logo" style={{ width: "auto", height: "30px" }} />
      </Stack>
      <Divider orientation="vertical" flexItem />
      <Typography variant="body1" noWrap color="secondary">
        {name}
      </Typography>
    </Stack>
  );
};
