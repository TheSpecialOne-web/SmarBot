import { Typography } from "@mui/material";

import { OptionsMenu, OptionsMenuItem } from "@/components/menus/OptionsMenu";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getIsGroupAdmin, getIsTenantAdmin } from "@/libs/permission";

type Props = {
  onClickStartChat: () => void;
  onClickArchive: () => void;
  groupId?: number;
};

export const AssistantsTableAction = ({ onClickStartChat, onClickArchive, groupId }: Props) => {
  const { userInfo } = useUserInfo();
  const isGroupAdmin = groupId
    ? getIsGroupAdmin({ userInfo, groupId })
    : getIsTenantAdmin(userInfo);

  const menuItems: OptionsMenuItem[] = [
    {
      onClick: onClickStartChat,
      children: <Typography variant="subtitle2">チャットを始める</Typography>,
    },
    {
      onClick: onClickArchive,
      disabled: !isGroupAdmin,
      tooltip: !isGroupAdmin
        ? {
            title: "アシスタントのアーカイブにはグループ管理者権限が必要です",
          }
        : undefined,
      children: <Typography variant="subtitle2">アーカイブする</Typography>,
    },
  ];

  return <OptionsMenu items={menuItems} />;
};
