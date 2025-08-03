import AndroidIcon from "@mui/icons-material/Android";
import ContentPasteIcon from "@mui/icons-material/ContentPaste";
import FestivalIcon from "@mui/icons-material/Festival";
import NotificationsIcon from "@mui/icons-material/Notifications";
import SupervisorAccountIcon from "@mui/icons-material/SupervisorAccount";
import { Box, Button, Link, Stack, Typography } from "@mui/material";
import { useLocation } from "react-router-dom";

import { MANAGEMENT_SIDEBAR_WIDTH, TOPBAR_HEIGHT } from "@/const";

export const AdministratorSidebar = () => {
  const location = useLocation();
  const selectedPath = "#" + location.pathname;

  const sidebarLinks = [
    {
      name: "テナント管理",
      path: "#/administrator/tenants",
      icon: <FestivalIcon />,
    },
    {
      name: "bot管理",
      path: "#/administrator/bots",
      icon: <AndroidIcon />,
    },
    {
      name: (
        <span>
          アシスタント
          <br />
          テンプレート
        </span>
      ),
      path: "#/administrator/assistant-templates",
      icon: <ContentPasteIcon />,
    },
    {
      name: "通知管理",
      path: "#/administrator/notifications",
      icon: <NotificationsIcon />,
    },
    {
      name: "運営者管理",
      path: "#/administrator/administrators",
      icon: <SupervisorAccountIcon />,
    },
  ];

  return (
    <Box
      sx={{
        height: `calc(100vh - ${TOPBAR_HEIGHT}px)`,
        borderRight: 1,
        borderColor: "grey.300",
        bgcolor: "background.paper",
      }}
      width={MANAGEMENT_SIDEBAR_WIDTH}
      minWidth={MANAGEMENT_SIDEBAR_WIDTH}
    >
      <Stack px={2} py={3} sx={{ width: "100%", height: "100%" }}>
        <Stack gap={2}>
          {sidebarLinks.map((link, index) => (
            <Button
              key={index}
              href={link.path}
              component={Link}
              color="inherit"
              startIcon={link.icon}
              fullWidth
              sx={{
                justifyContent: "flex-start",
                color: selectedPath.startsWith(link.path) ? "primary.main" : "inherit",
                py: 1,
              }}
            >
              <Typography variant="h5">{link.name}</Typography>
            </Button>
          ))}
        </Stack>
      </Stack>
    </Box>
  );
};
