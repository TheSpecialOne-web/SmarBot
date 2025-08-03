import { useAuth0 } from "@auth0/auth0-react";
import { Box, Stack } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { Outlet } from "react-router-dom";

import { MaintenanceModal } from "@/components/modals/MaintenanceModal";
import { TOPBAR_HEIGHT } from "@/const";
import { useUserInfo } from "@/hooks/useUserInfo";
import { Header } from "@/modules/layouts/headers/Header";
import { LayoutContainer } from "@/modules/layouts/LayoutContainer";
import { ManagementSidebar } from "@/modules/layouts/sidebars/ManagementSidebar";

export const ManagementLayout = () => {
  const { maintenanceMode } = useFlags();
  const { userInfo } = useUserInfo();
  const { logout } = useAuth0();

  const onLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  return (
    <Box sx={{ height: 1 }}>
      <Header activePage="tenantManagement" userInfo={userInfo} onLogout={onLogout} />
      <LayoutContainer tenant={userInfo.tenant}>
        <Stack direction="row">
          <ManagementSidebar userInfo={userInfo} />
          <Box flex={1} height={`calc(100vh - ${TOPBAR_HEIGHT}px)`} overflow="auto">
            <Outlet />
          </Box>
        </Stack>
      </LayoutContainer>
      {maintenanceMode && <MaintenanceModal />}
    </Box>
  );
};
