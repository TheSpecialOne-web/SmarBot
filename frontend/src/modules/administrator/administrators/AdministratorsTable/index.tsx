import FiberNewIcon from "@mui/icons-material/FiberNew";
import { Stack, Typography } from "@mui/material";
import dayjs from "dayjs";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Administrator } from "@/orval/models/administrator-api";

type Props = {
  administrators: Administrator[];
  refetchAdministrators: () => void;
};

const filterAdministrator = (administrators: Administrator[], query: string) => {
  return administrators.filter(administrator => {
    return filterTest(query, [administrator.name, administrator.email]);
  });
};

const sortAdministrators = (
  administrators: Administrator[],
  order: Order,
  orderBy: keyof Administrator,
) => {
  const comparator = getComparator<Administrator>(order, orderBy);
  return [...administrators].sort(comparator);
};

const tableColumns: CustomTableColumn<Administrator>[] = [
  {
    key: "name",
    label: "運営者名",
    align: "left",
    render: row => {
      const isNew = dayjs().diff(dayjs(row.created_at), "day") < 7;
      return (
        <Stack direction="row" gap={0.5}>
          <Typography>{row.name}</Typography>
          {isNew && <FiberNewIcon color="primary" />}
        </Stack>
      );
    },
    sortFunction: sortAdministrators,
  },
  {
    key: "email",
    label: "メールアドレス",
    align: "left",
    sortFunction: sortAdministrators,
  },
  {
    key: "created_at",
    label: "登録日",
    align: "left",
    render: row => {
      return <Typography>{dayjs(row.created_at).format("YYYY年M月D日 HH:mm:ss")}</Typography>;
    },
    sortFunction: sortAdministrators,
  },
];

export const AdministratorsTable = ({ administrators }: Props) => {
  return (
    <CustomTable<Administrator>
      tableColumns={tableColumns}
      tableData={administrators}
      searchFilter={filterAdministrator}
      defaultSortProps={{ key: "created_at", order: "desc" }}
    />
  );
};
