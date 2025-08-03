import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import { Stack, Typography } from "@mui/material";
import { useRef } from "react";

import { OptionsMenu } from "@/components/menus/OptionsMenu";

type Props = {
  onChangeTitle: () => void;
  onDelete: () => void;
};

export const ConversationActionButton = ({ onChangeTitle, onDelete }: Props) => {
  const optionsMenuRef = useRef<{ handleClose: () => void }>(null);

  const menuItems = [
    {
      onClick: () => {
        optionsMenuRef.current?.handleClose();
        onChangeTitle();
      },
      children: (
        <Stack direction="row" alignItems="center" gap={1}>
          <EditOutlinedIcon color="inherit" fontSize="small" />
          <Typography variant="caption">タイトル変更</Typography>
        </Stack>
      ),
    },
    {
      onClick: onDelete,
      children: (
        <Stack direction="row" alignItems="center" gap={1}>
          <DeleteOutlineOutlinedIcon color="error" fontSize="small" />
          <Typography variant="caption" color="error">
            削除
          </Typography>
        </Stack>
      ),
    },
  ];

  return (
    <OptionsMenu
      ref={optionsMenuRef}
      items={menuItems}
      icon={<MoreHorizIcon fontSize="small" />}
      buttonSx={{
        p: 0.5,
      }}
    />
  );
};
