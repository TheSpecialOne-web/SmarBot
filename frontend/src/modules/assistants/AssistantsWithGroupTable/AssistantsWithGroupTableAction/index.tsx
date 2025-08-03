import { Typography } from "@mui/material";

import { OptionsMenu, OptionsMenuItem } from "@/components/menus/OptionsMenu";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getIsGroupAdmin } from "@/libs/permission";

type Props = {
  onClickStartChat: () => void;
  onClickArchive: () => void;
  groupId: number;
};

export const AssistantsWithGroupTableAction = ({
  onClickStartChat,
  onClickArchive,
  groupId,
}: Props) => {
  const { userInfo } = useUserInfo();
  const isGroupAdmin = getIsGroupAdmin({ userInfo, groupId });

  const menuItems: OptionsMenuItem[] = [
    {
      onClick: onClickStartChat,
      children: <Typography fontSize={14}>チャットを始める</Typography>,
    },
    {
      onClick: onClickArchive,
      disabled: !isGroupAdmin,
      tooltip: !isGroupAdmin
        ? {
            title: "アシスタントのアーカイブにはグループ管理者権限が必要です",
          }
        : undefined,
      children: <Typography fontSize={14}>アーカイブする</Typography>,
    },
  ];

  return <OptionsMenu items={menuItems} />;
};
