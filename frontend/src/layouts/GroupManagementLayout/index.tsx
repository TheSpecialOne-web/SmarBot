import { useAuth0 } from "@auth0/auth0-react";
import { Box, Stack } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { Outlet, useParams } from "react-router-dom";

import { MaintenanceModal } from "@/components/modals/MaintenanceModal";
import { TOPBAR_HEIGHT } from "@/const";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { getIsGroupAdmin, getIsTenantAdmin } from "@/libs/permission";
import { Header } from "@/modules/layouts/headers/Header";
import { LayoutContainer } from "@/modules/layouts/LayoutContainer";
import { GroupManagementSidebar } from "@/modules/layouts/sidebars/GroupManagementSidebar";
import { useGetGroups } from "@/orval/backend-api";

export const GroupManagementLayout = () => {
  const { maintenanceMode } = useFlags();
  const { userInfo } = useUserInfo();
  const { logout } = useAuth0();
  const params = useParams<{ groupId: string }>();
  const groupId = Number(params.groupId);
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const { data: groupsData, error: getGroupsError } = useGetGroups({
    swr: { enabled: getIsTenantAdmin(userInfo) },
  });
  if (getGroupsError) {
    const errMsg = getErrorMessage(getGroupsError);
    enqueueErrorSnackbar({ message: errMsg || "グループの取得に失敗しました。" });
  }
  const groups = getIsTenantAdmin(userInfo) ? groupsData?.groups ?? [] : userInfo.groups;

  const onLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  return (
    <Box sx={{ height: 1 }}>
      <Header activePage="groupManagement" userInfo={userInfo} onLogout={onLogout} />
      <LayoutContainer tenant={userInfo.tenant}>
        <Stack direction="row">
          <GroupManagementSidebar
            groupId={groupId}
            groups={groups.sort((a, b) =>
              // is_general が true のものを先頭に表示
              a.is_general === b.is_general ? 0 : a.is_general ? -1 : 1,
            )}
            isGroupAdmin={getIsGroupAdmin({ userInfo, groupId })}
          />
          <Box flex={1} height={`calc(100vh - ${TOPBAR_HEIGHT}px)`} overflow="auto">
            <Outlet />
          </Box>
        </Stack>
      </LayoutContainer>
      {maintenanceMode && <MaintenanceModal />}
    </Box>
  );
};
