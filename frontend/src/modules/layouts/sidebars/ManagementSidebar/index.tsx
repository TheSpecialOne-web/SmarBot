import GroupsIcon from "@mui/icons-material/Groups";
import ManageAccountsIcon from "@mui/icons-material/ManageAccounts";
import PersonIcon from "@mui/icons-material/Person";
import SpaceDashboardIcon from "@mui/icons-material/SpaceDashboard";
import { Box, Button, Link, Stack, Typography } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { RiRobot2Fill } from "react-icons/ri";
import { useLocation } from "react-router-dom";

import { MANAGEMENT_SIDEBAR_WIDTH, TOPBAR_HEIGHT } from "@/const";
import { getIsTenantAdmin } from "@/libs/permission";
import { UserInfo } from "@/orval/models/backend-api";

type Props = {
  userInfo: UserInfo;
};

export const ManagementSidebar = ({ userInfo }: Props) => {
  const location = useLocation();

  const selectedPath = "#" + location.pathname;

  const isTenantAdmin = getIsTenantAdmin(userInfo);

  const { usageDashboard } = useFlags();

  const sidebarLinks = [
    {
      name: "アシスタント",
      path: "#/main/assistants",
      icon: <RiRobot2Fill />,
    },
    ...(isTenantAdmin
      ? [
          {
            name: "ユーザー",
            path: "#/main/users",
            icon: <PersonIcon />,
          },
          {
            name: "ユーザーグループ",
            path: "#/main/groups",
            icon: <GroupsIcon />,
          },
          {
            name: "組織設定",
            path: "#/main/tenant-settings",
            icon: <ManageAccountsIcon />,
          },
          ...(usageDashboard
            ? [
                {
                  name: "利用量分析",
                  path: "#/main/usage",
                  icon: <SpaceDashboardIcon />,
                },
              ]
            : []),
        ]
      : []),
  ];

  return (
    <Box
      sx={{
        height: `calc(100vh - ${TOPBAR_HEIGHT}px)`,
        borderRight: 1,
        borderColor: "grey.300",
        bgcolor: "background.paper",
        overflowY: "auto",
      }}
      width={MANAGEMENT_SIDEBAR_WIDTH}
      minWidth={MANAGEMENT_SIDEBAR_WIDTH}
    >
      <Stack px={2} py={3} sx={{ width: "100%", height: "100%" }}>
        <Typography fontWeight={600} color="secondary" variant="subtitle2" mb={0.5}>
          組織管理
        </Typography>
        <Stack gap={0.5} flex={1}>
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
