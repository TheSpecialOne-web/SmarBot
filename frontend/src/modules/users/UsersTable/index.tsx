import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { useUserInfo } from "@/hooks/useUserInfo";
import { filterUserByRole } from "@/libs/columnFilter";
import { filterUser } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Role, User } from "@/orval/models/backend-api";

import { UsersTableAction } from "./UsersTableAction";

export const sortUsers = (users: User[], order: Order, orderBy: keyof User) => {
  const comparator = getComparator<User>(order, orderBy);
  return [...users].sort(comparator);
};

const tableColumns: CustomTableColumn<User>[] = [
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
    key: "roles",
    label: "役割",
    align: "left",
    render: user => {
      const role = user.roles.includes(Role.admin) ? "組織管理者" : "一般ユーザー";
      return role;
    },
    columnFilterProps: {
      filterItems: [
        { label: "組織管理者", key: Role.admin },
        { label: "一般ユーザー", key: Role.user },
      ],
      filterFunction: filterUserByRole,
    },
  },
];

type Props = {
  users: User[];
  onClickUpdateIcon: (user: User) => void;
  onClickDeleteIcon: (user: User) => void;
};

export const UsersTable = ({ users, onClickUpdateIcon, onClickDeleteIcon }: Props) => {
  const { userInfo } = useUserInfo();

  const renderActionColumn = (user: User) => {
    return (
      <UsersTableAction
        user={user}
        onClickEdit={() => onClickUpdateIcon(user)}
        onClickDelete={() => onClickDeleteIcon(user)}
        canDelete={userInfo.id === user.id}
      />
    );
  };

  return (
    <CustomTable<User>
      tableColumns={tableColumns}
      tableData={users}
      searchFilter={filterUser}
      defaultSortProps={{ key: "name", order: "asc" }}
      renderActionColumn={renderActionColumn}
    />
  );
};
