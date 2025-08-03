import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { GroupUser, User } from "@/orval/models/backend-api";

const searchFilter = (users: User[], query: string) => {
  return users.filter(user => {
    return filterTest(query, [user.name, user.email]);
  });
};

const filterGroupUsers = (allUsers: User[], groupUsers: GroupUser[]) => {
  return allUsers.filter(user => !groupUsers.some(groupUser => groupUser.id === user.id));
};

const sortUsers = (users: User[], order: Order, orderBy: keyof User) => {
  const comparator = getComparator<User>(order, orderBy);
  return [...users].sort(comparator);
};

type Props = {
  groupUsers: GroupUser[];
  allUsers: User[];
  selectedUserIds: number[];
  setSelectedUserIds: (userIds: number[]) => void;
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
];

export const AddUsersToGroupTable = ({
  groupUsers,
  allUsers,
  selectedUserIds,
  setSelectedUserIds,
}: Props) => {
  const filteredUsers = filterGroupUsers(allUsers, groupUsers);

  return (
    <CustomTable<User>
      tableColumns={tableColumns}
      tableData={filteredUsers}
      searchFilter={searchFilter}
      checkboxProps={{
        selectedRowIds: selectedUserIds,
        setSelectedRowIds: setSelectedUserIds,
      }}
    />
  );
};
