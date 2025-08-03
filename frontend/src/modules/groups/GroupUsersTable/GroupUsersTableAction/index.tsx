import { Typography } from "@mui/material";

import { OptionsMenu, OptionsMenuItem } from "@/components/menus/OptionsMenu";

type Props = {
  isGeneralGroup: boolean;
  isTenantAdmin: boolean;
  isSelf: boolean;
  onClickUpdateUserGroupRole: () => void;
  onClickDeleteGroupUser: () => void;
};

export const GroupUsersTableAction = ({
  isGeneralGroup,
  isTenantAdmin,
  isSelf,
  onClickUpdateUserGroupRole,
  onClickDeleteGroupUser,
}: Props) => {
  const menuItems: OptionsMenuItem[] = [
    {
      onClick: onClickUpdateUserGroupRole,
      disabled: isTenantAdmin,
      tooltip: isTenantAdmin
        ? {
            title: "組織管理者のグループ権限は変更できません",
          }
        : undefined,
      children: <Typography variant="body2">権限を変更する</Typography>,
    },
    {
      onClick: onClickDeleteGroupUser,
      disabled: isGeneralGroup,
      tooltip: isGeneralGroup
        ? {
            title: "Allグループからは削除できません",
          }
        : undefined,
      children: <Typography variant="body2">グループから削除する</Typography>,
    },
  ];

  return <OptionsMenu items={menuItems} disabled={isSelf} />;
};
