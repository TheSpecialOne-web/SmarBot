import ExpandMoreRoundedIcon from "@mui/icons-material/ExpandMoreRounded";
import PersonIcon from "@mui/icons-material/Person";
import { Box, Button, Link, MenuItem, Select, Stack, styled, Typography } from "@mui/material";
import { RiRobot2Fill } from "react-icons/ri";
import { useLocation, useNavigate } from "react-router-dom";

import { MANAGEMENT_SIDEBAR_WIDTH, TOPBAR_HEIGHT } from "@/const";
import { Group } from "@/orval/models/backend-api";
import { theme } from "@/theme";

const StyledSelect = styled(Select<number>)(() => ({
  fontWeight: "bold",
  fontSize: "16px",
  ":hover": {
    backgroundColor: theme.palette.onHover.main,
  },
  // 枠を消す
  ".MuiOutlinedInput-notchedOutline": {
    border: 0,
  },
  // フォーカス時の枠を消す
  "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
    border: 0,
  },
  ".MuiOutlinedInput-input": {
    padding: "8px",
  },
}));

const getSidebarLinks = (groupId: number, isGroupAdmin: boolean) => [
  {
    name: "アシスタント",
    path: `#/main/groups/${groupId}/assistants`,
    icon: <RiRobot2Fill />,
  },
  ...(isGroupAdmin
    ? [
        {
          name: "ユーザー",
          path: `#/main/groups/${groupId}/users`,
          icon: <PersonIcon />,
        },
      ]
    : []),
];

type Props = {
  groupId: number;
  groups: Group[];
  isGroupAdmin: boolean;
};

export const GroupManagementSidebar = ({ groupId, groups, isGroupAdmin }: Props) => {
  const location = useLocation();
  const navigate = useNavigate();
  const selectedPath = "#" + location.pathname;

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
      <Stack px={2} py={3} gap={0.5} sx={{ width: "100%", height: "100%" }}>
        <Typography fontWeight={600} color="secondary" variant="subtitle2" mb={0.5}>
          グループ管理
        </Typography>
        <StyledSelect
          value={groupId || ""}
          onChange={event => {
            const groupId = event.target.value;
            navigate(`/main/groups/${groupId}/assistants`);
          }}
          IconComponent={ExpandMoreRoundedIcon}
        >
          {groups.map(group => (
            <MenuItem key={group.id} value={group.id}>
              {group.name}
            </MenuItem>
          ))}
        </StyledSelect>
        {getSidebarLinks(groupId, isGroupAdmin).map((link, index) => (
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
    </Box>
  );
};
