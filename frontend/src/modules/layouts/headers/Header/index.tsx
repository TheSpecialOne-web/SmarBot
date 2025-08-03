import BusinessIcon from "@mui/icons-material/Business";
import GroupIcon from "@mui/icons-material/Group";
import LogoDevIcon from "@mui/icons-material/LogoDev";
import QuestionAnswerIcon from "@mui/icons-material/QuestionAnswer";
import SettingsIcon from "@mui/icons-material/Settings";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import { Stack, Typography } from "@mui/material";
import { grey } from "@mui/material/colors";
import { useNavigate } from "react-router-dom";

import logo from "@/assets/logo.png";
import { OptionsMenu } from "@/components/menus/OptionsMenu";
import { useScreen } from "@/hooks/useScreen";
import { UserInfo } from "@/orval/models/backend-api";

import { HeaderAccountMenu } from "../HeaderAccountMenu";
import { HeaderButton } from "../HeaderButton";
import { HeaderContainer } from "../HeaderContainer";
import { HeaderLogo } from "../HeaderLogo";
import { NotificationButtonWithDrawer } from "../NotificationButtonWithDrawer";

type PageType = "administrator" | "chat" | "groupManagement" | "tenantManagement";

type Props = {
  activePage: PageType;
  userInfo: UserInfo;
  onLogout: () => void;
};

export const Header = ({ activePage, userInfo, onLogout }: Props) => {
  const { isMobile } = useScreen();
  const navigate = useNavigate();
  const isAdministrator = userInfo.is_administrator;
  const isAdministratorPage = activePage === "administrator";

  const generalGroup = userInfo.groups.find(group => group.is_general);

  return (
    <HeaderContainer
      bgcolor={isAdministratorPage ? "administratorHeaderBackground.main" : "background.paper"}
    >
      <HeaderLogo
        logoUrl={userInfo.tenant.logo_url || logo}
        name={
          isAdministratorPage ? (
            <Stack direction="row">
              <WarningAmberRoundedIcon color="warning" />
              <Typography
                variant="h1"
                sx={{
                  px: 1,
                  fontSize: 20,
                  fontWeight: 600,
                }}
              >
                運営画面
              </Typography>
              <WarningAmberRoundedIcon color="warning" />
            </Stack>
          ) : (
            userInfo.tenant.name
          )
        }
      />
      <Stack direction="row" alignItems="center" gap={2}>
        {isAdministrator && (
          <HeaderButton
            icon={<LogoDevIcon />}
            text="運営画面"
            href="#/administrator/tenants"
            isActive={isAdministratorPage}
          />
        )}
        {!isMobile && (
          <>
            <HeaderButton
              icon={<QuestionAnswerIcon />}
              text="チャット"
              href="#/main/chat"
              isActive={activePage === "chat"}
            />
            <OptionsMenu
              items={[
                {
                  onClick: () => navigate(`/main/groups/${generalGroup?.id}/assistants`),
                  children: (
                    <Stack direction="row" alignItems="center" gap={1}>
                      <GroupIcon />
                      <Typography>グループ管理</Typography>
                    </Stack>
                  ),
                  sx: { color: activePage === "groupManagement" ? "primary.main" : grey[900] },
                },
                {
                  onClick: () => navigate("/main/assistants"),
                  children: (
                    <Stack direction="row" alignItems="center" gap={1}>
                      <BusinessIcon />
                      <Typography>組織管理</Typography>
                    </Stack>
                  ),
                  sx: { color: activePage === "tenantManagement" ? "primary.main" : grey[900] },
                },
              ]}
              icon={
                <Stack direction="column" alignItems="center">
                  <SettingsIcon />
                  <Typography fontSize={10}>管理画面</Typography>
                </Stack>
              }
              buttonSx={{
                py: 0.5,
                color: ["groupManagement", "tenantManagement"].includes(activePage)
                  ? "primary.main"
                  : grey[900],
                borderRadius: 1,
              }}
            />
          </>
        )}
        <NotificationButtonWithDrawer />
        <HeaderAccountMenu userInfo={userInfo} onClickLogout={onLogout} />
      </Stack>
    </HeaderContainer>
  );
};
