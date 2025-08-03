import { useAuth0 } from "@auth0/auth0-react";
import ShortTextIcon from "@mui/icons-material/ShortText";
import { Box, Drawer, IconButton, Stack } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { Fragment } from "react";
import { Outlet } from "react-router-dom";

import { MaintenanceModal } from "@/components/modals/MaintenanceModal";
import { CHAT_LAYOUT_SIDEBAR_WIDTH, TOPBAR_HEIGHT } from "@/const";
import { useBot } from "@/hooks/useBot";
import { useConversation } from "@/hooks/useConversation";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useScreen } from "@/hooks/useScreen";
import { useUserInfo } from "@/hooks/useUserInfo";
import { Header } from "@/modules/layouts/headers/Header";
import { LayoutContainer } from "@/modules/layouts/LayoutContainer";
import { ChatSidebar } from "@/modules/layouts/sidebars/ChatSidebar";
import { SidebarToggleButton } from "@/modules/layouts/sidebars/SidebarToggleButton";

export const ChatLayout = () => {
  const { maintenanceMode } = useFlags();
  const { userInfo } = useUserInfo();
  const { logout } = useAuth0();
  const { reorderBots, chatGptBots, assistants, isLoadingFetchBots } = useBot();
  const { conversations, isLoadingFetchConversations } = useConversation();

  const { isTablet } = useScreen();
  const {
    isOpen: isSidebarOpen,
    close: closeSidebar,
    toggle: toggleSidebar,
  } = useDisclosure({
    initialState: !isTablet,
  });

  const onLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  return (
    <Box sx={{ height: 1 }}>
      <Header activePage="chat" userInfo={userInfo} onLogout={onLogout} />
      <LayoutContainer tenant={userInfo.tenant}>
        <Stack direction="row" position="relative">
          {isTablet ? (
            <Drawer
              open={isSidebarOpen}
              onClose={closeSidebar}
              sx={{
                "& .MuiDrawer-paperAnchorLeft": {
                  width: CHAT_LAYOUT_SIDEBAR_WIDTH,
                  top: TOPBAR_HEIGHT,
                  height: `calc(100% - ${TOPBAR_HEIGHT}px)`,
                },
                zIndex: 10,
              }}
            >
              <ChatSidebar
                chatGptBots={chatGptBots}
                assistants={assistants}
                conversations={conversations}
                reorderBots={reorderBots}
                onClose={closeSidebar}
                toggleShowSidebar={toggleSidebar}
                isLoadingFetchBots={isLoadingFetchBots}
                isLoadingFetchConversations={isLoadingFetchConversations}
              />
            </Drawer>
          ) : (
            <Fragment>
              {isSidebarOpen && (
                <ChatSidebar
                  chatGptBots={chatGptBots}
                  assistants={assistants}
                  conversations={conversations}
                  reorderBots={reorderBots}
                  onClose={closeSidebar}
                  toggleShowSidebar={toggleSidebar}
                  isLoadingFetchBots={isLoadingFetchBots}
                  isLoadingFetchConversations={isLoadingFetchConversations}
                />
              )}
            </Fragment>
          )}
          <Box
            flex={1}
            position="relative"
            height={`calc(100vh - ${TOPBAR_HEIGHT}px)`}
            overflow="auto"
          >
            {isTablet && (
              <SidebarToggleButton isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
            )}
            {!isTablet && !isSidebarOpen && (
              <IconButton
                onClick={toggleSidebar}
                sx={{
                  position: "absolute",
                  zIndex: 999,
                }}
              >
                <ShortTextIcon />
              </IconButton>
            )}
            <Outlet />
          </Box>
        </Stack>
      </LayoutContainer>
      {maintenanceMode && <MaintenanceModal />}
    </Box>
  );
};
