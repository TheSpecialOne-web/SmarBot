import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import { IconButton, Menu, MenuItem, Tooltip, Typography } from "@mui/material";
import { MouseEvent, useState } from "react";

import { User } from "@/orval/models/backend-api";

type Props = {
  user: User;
  onClickEdit: () => void;
  onClickDelete: () => void;
  canDelete: boolean;
};

export const UsersTableAction = ({ user, onClickEdit, onClickDelete, canDelete }: Props) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const handleClick = (event: MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <>
      <IconButton onClick={handleClick}>
        <MoreHorizIcon />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        MenuListProps={{
          sx: {
            p: 0.5,
          },
        }}
      >
        <MenuItem onClick={onClickEdit}>
          <Typography variant="subtitle2">ユーザー情報編集</Typography>
        </MenuItem>
        <Tooltip title={canDelete && "自分自身は削除できません"}>
          <span>
            <MenuItem onClick={onClickDelete} disabled={canDelete}>
              <Typography variant="subtitle2">ユーザー削除</Typography>
            </MenuItem>
          </span>
        </Tooltip>
        {!user.roles.includes("admin") && (
          <MenuItem href={`/#/main/users/${user.id}`} component="a">
            <Typography variant="subtitle2">アシスタント権限編集</Typography>
          </MenuItem>
        )}
      </Menu>
    </>
  );
};
