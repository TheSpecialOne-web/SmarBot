import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { useUserInfo } from "@/hooks/useUserInfo";
import { groupRoleToJapanese } from "@/libs/group";
import { getIsGroupAdmin } from "@/libs/permission";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Group, GroupRole, GroupUser, Role } from "@/orval/models/backend-api";

import { GroupUsersTableAction } from "./GroupUsersTableAction";

export const searchFilter = (users: GroupUser[], query: string) => {
  return users.filter(user => {
    return filterTest(query, [user.name, user.email]);
  });
};

const sortUsers = (users: GroupUser[], order: Order, orderBy: keyof GroupUser) => {
  const comparator = getComparator<GroupUser>(order, orderBy);
  return [...users].sort(comparator);
};

const filterUsersByGroupRole = (users: GroupUser[], queries: string[]) => {
  if (queries.length === 0) {
    return [];
  }

  return users.filter(user => {
    // 組織管理者はグループ管理者として扱う
    if (user.roles.includes(Role.admin)) {
      return queries.includes(GroupRole.group_admin);
    }
    return queries.includes(user.group_role);
  });
};

type Props = {
  group: Group;
  users: GroupUser[];
  onClickUpdateUserGroupRole: (user: GroupUser) => void;
  onClickDeleteGroupUser: (user: GroupUser) => void;
};

const tableColumns: CustomTableColumn<GroupUser>[] = [
  {
    key: "name",
    label: "ユーザー名",
    align: "left",
    sortFunction: sortUsers,
  },
  {
    key: "email",
    label: "メールアドレス",
    align: "left",
    sortFunction: sortUsers,
  },
  {
    key: "group_role",
    label: "権限",
    align: "left",
    render: (groupUser: GroupUser) => {
      return groupUser.roles.includes(Role.admin)
        ? "グループ管理者 (組織管理者)"
        : groupRoleToJapanese(groupUser.group_role);
    },
    columnFilterProps: {
      filterItems: Object.values(GroupRole).map(groupRole => ({
        label: groupRoleToJapanese(groupRole),
        key: groupRole,
      })),
      filterFunction: filterUsersByGroupRole,
    },
  },
];

export const GroupUsersTable = ({
  group,
  users,
  onClickUpdateUserGroupRole,
  onClickDeleteGroupUser,
}: Props) => {
  const { id, is_general: isGeneralGroup } = group;

  const { userInfo } = useUserInfo();
  const isGroupAdmin = getIsGroupAdmin({ userInfo, groupId: id });

  const renderActionColumn = (user: GroupUser) => {
    return (
      <GroupUsersTableAction
        isGeneralGroup={isGeneralGroup}
        isTenantAdmin={user.roles.includes(Role.admin)}
        isSelf={userInfo.id === user.id}
        onClickUpdateUserGroupRole={() => onClickUpdateUserGroupRole(user)}
        onClickDeleteGroupUser={() => onClickDeleteGroupUser(user)}
      />
    );
  };

  return (
    <CustomTable<GroupUser>
      tableColumns={tableColumns}
      tableData={users}
      searchFilter={searchFilter}
      defaultSortProps={{ key: "name", order: "asc" }}
      renderActionColumn={isGroupAdmin ? renderActionColumn : undefined}
    />
  );
};
