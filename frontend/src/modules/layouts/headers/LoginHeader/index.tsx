import { Typography } from "@mui/material";

import { TOPBAR_HEIGHT } from "@/const";

import { HeaderContainer } from "../HeaderContainer";

export const LoginHeader = () => {
  return (
    <HeaderContainer height={TOPBAR_HEIGHT}>
      <Typography variant="h4">neoAI Chat</Typography>
      <Typography variant="h4">by neoAI Inc.</Typography>
    </HeaderContainer>
  );
};
