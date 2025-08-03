import { useAuth0 } from "@auth0/auth0-react";
import { Box, Stack } from "@mui/material";
import { Outlet } from "react-router-dom";

import { TOPBAR_HEIGHT } from "@/const";
import { useUserInfo } from "@/hooks/useUserInfo";
import { Header } from "@/modules/layouts/headers/Header";
import { LayoutContainer } from "@/modules/layouts/LayoutContainer";
import { AdministratorSidebar } from "@/modules/layouts/sidebars/AdministratorSidebar";

export const AdministratorLayout = () => {
  const { userInfo } = useUserInfo();
  const { logout } = useAuth0();

  const onLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  return (
    <Box sx={{ height: 1 }}>
      <Header activePage="administrator" userInfo={userInfo} onLogout={onLogout} />
      <LayoutContainer>
        <Stack direction="row">
          <AdministratorSidebar />
          <Box flex={1} height={`calc(100vh - ${TOPBAR_HEIGHT}px)`} overflow="auto">
            <Outlet />
          </Box>
        </Stack>
      </LayoutContainer>
    </Box>
  );
};
