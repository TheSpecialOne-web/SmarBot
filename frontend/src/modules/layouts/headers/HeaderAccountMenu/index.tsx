import { Email } from "@mui/icons-material";
import AccountCircle from "@mui/icons-material/AccountCircle";
import LogoutIcon from "@mui/icons-material/Logout";
import { Button, Menu, Stack, Typography } from "@mui/material";
import { grey } from "@mui/material/colors";
import { useState } from "react";

import { UserInfo } from "@/orval/models/backend-api";

type Props = {
  userInfo: UserInfo;
  onClickLogout: () => void;
};

export const HeaderAccountMenu = ({ userInfo, onClickLogout }: Props) => {
  const [openMenu, setOpenMenu] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const onOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    setOpenMenu(true);
  };

  const onClose = () => {
    setAnchorEl(null);
    setOpenMenu(false);
  };

  return (
    <>
      <Button
        color="inherit"
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          color: grey[900],
          py: 0.5,
        }}
        onClick={openMenu ? onClose : onOpen}
      >
        <AccountCircle />
        <Typography fontSize={10} whiteSpace="nowrap">
          アカウント
        </Typography>
      </Button>
      <Menu
        id="account-menu"
        anchorEl={anchorEl}
        open={openMenu}
        onClose={onClose}
        onClick={onClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        sx={{
          "& .MuiPaper-root": {
            borderRadius: 1,
            px: 4,
            pt: 1,
          },
        }}
      >
        <Stack
          justifyItems="center"
          alignItems="center"
          sx={{
            pb: 1,
          }}
        >
          <Typography variant="h4" noWrap color="secondary">
            {userInfo.name}
          </Typography>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Email
              color="secondary"
              sx={{
                fontSize: 14,
              }}
            />
            <Typography variant="caption" noWrap color="secondary">
              {userInfo.email}
            </Typography>
          </Stack>
        </Stack>
        <Button
          fullWidth
          onClick={onClickLogout}
          color="secondary"
          startIcon={<LogoutIcon fontSize="small" />}
        >
          <Typography variant="subtitle2" color="secondary">
            ログアウト
          </Typography>
        </Button>
      </Menu>
    </>
  );
};
