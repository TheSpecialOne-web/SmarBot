import { Typography } from "@mui/material";

import { OptionsMenu, OptionsMenuItem } from "@/components/menus/OptionsMenu";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getIsGroupAdmin } from "@/libs/permission";
import { BotStatus, BotWithGroup } from "@/orval/models/backend-api";

type Props = {
  bot: BotWithGroup;
  onClickRestore: (bot: BotWithGroup) => void;
  onClickDelete: (bot: BotWithGroup) => void;
};

export const ArchivedAssistantsWithGroupTableAction = ({
  bot,
  onClickRestore,
  onClickDelete,
}: Props) => {
  const { userInfo } = useUserInfo();
  const isGroupAdmin = getIsGroupAdmin({
    userInfo,
    groupId: bot.group_id,
  });

  const menuItems: OptionsMenuItem[] = [
    {
      onClick: () => onClickDelete(bot),
      disabled: !isGroupAdmin,
      tooltip: !isGroupAdmin
        ? { title: "アシスタントを削除するにはグループ管理者権限が必要です。" }
        : undefined,
      children: <Typography fontSize={14}>削除する</Typography>,
    },
    {
      onClick: () => onClickRestore(bot),
      disabled: !isGroupAdmin,
      tooltip: !isGroupAdmin
        ? { title: "アシスタントを復元するにはグループ管理者権限が必要です。" }
        : undefined,
      children: <Typography fontSize={14}>復元する</Typography>,
    },
  ];

  return <OptionsMenu items={menuItems} disabled={bot.status === BotStatus.deleting} />;
};
