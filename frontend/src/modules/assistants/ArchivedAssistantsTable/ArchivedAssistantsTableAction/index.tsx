import { Typography } from "@mui/material";

import { OptionsMenu, OptionsMenuItem } from "@/components/menus/OptionsMenu";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getIsGroupAdmin, getIsTenantAdmin } from "@/libs/permission";
import { Bot, BotStatus } from "@/orval/models/backend-api";

type Props = {
  bot: Bot;
  onClickRestore: (bot: Bot) => void;
  onClickDelete: (bot: Bot) => void;
  groupId?: number;
};

export const ArchivedAssistantsTableAction = ({
  bot,
  onClickRestore,
  onClickDelete,
  groupId,
}: Props) => {
  const { userInfo } = useUserInfo();
  const isGroupAdmin = groupId
    ? getIsGroupAdmin({ userInfo, groupId })
    : getIsTenantAdmin(userInfo);

  const menuItems: OptionsMenuItem[] = [
    {
      onClick: () => onClickDelete(bot),
      disabled: !isGroupAdmin,
      tooltip: !isGroupAdmin
        ? { title: "アシスタントを削除するにはグループ管理者権限が必要です。" }
        : undefined,
      children: <Typography variant="subtitle2">削除する</Typography>,
    },
    {
      onClick: () => onClickRestore(bot),
      disabled: !isGroupAdmin,
      tooltip: !isGroupAdmin
        ? { title: "アシスタントを復元するにはグループ管理者権限が必要です。" }
        : undefined,
      children: <Typography variant="subtitle2">復元する</Typography>,
    },
  ];

  return <OptionsMenu items={menuItems} disabled={bot.status === BotStatus.deleting} />;
};
