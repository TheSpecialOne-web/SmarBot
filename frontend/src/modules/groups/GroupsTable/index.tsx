import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { IconButton, Link, Stack } from "@mui/material";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterGroup } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Group } from "@/orval/models/backend-api";
import { formatDate } from "@/utils/formatDate";

const sortGroups = (groups: Group[], order: Order, orderBy: keyof Group) => {
  const comparator = getComparator<Group>(order, orderBy);
  return [...groups].sort(comparator);
};

const tableColumns: CustomTableColumn<Group>[] = [
  {
    key: "name",
    label: "グループ名",
    align: "left",
    render: item => <Link href={`#/main/groups/${item.id}/assistants`}>{item.name}</Link>,
    sortFunction: sortGroups,
  },
  {
    key: "created_at",
    label: "作成日時",
    align: "left",
    render: group => {
      return formatDate(group.created_at);
    },
    sortFunction: sortGroups,
  },
];

type Props = {
  groups: Group[];
  onClickUpdateIcon: (group: Group) => void;
  onClickDeleteIcon: (group: Group) => void;
};

export const GroupsTable = ({ groups, onClickUpdateIcon, onClickDeleteIcon }: Props) => {
  const renderActionColumn = (group: Group) => {
    return (
      <Stack direction="row" gap={1} justifyContent="right">
        <IconButton onClick={() => onClickUpdateIcon(group)} disabled={group.is_general}>
          <EditOutlinedIcon color={group.is_general ? "disabled" : "primary"} />
        </IconButton>
        <IconButton onClick={() => onClickDeleteIcon(group)} disabled={group.is_general}>
          <DeleteOutlineOutlinedIcon color={group.is_general ? "disabled" : "error"} />
        </IconButton>
      </Stack>
    );
  };

  return (
    <CustomTable<Group>
      tableColumns={tableColumns}
      tableData={groups}
      searchFilter={filterGroup}
      defaultSortProps={{ key: "name", order: "asc" }}
      renderActionColumn={renderActionColumn}
    />
  );
};
