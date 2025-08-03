import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import { Link, Stack } from "@mui/material";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Tenant } from "@/orval/models/administrator-api";

type Props = {
  tenants: Tenant[];
  refetchTenants: () => void;
  onCreatePanelOpen: () => void;
  onDeleteClick: (tenant: Tenant) => void;
};

const filterAdministratorTenant = (tenants: Tenant[], query: string) => {
  return tenants.filter(tenant => {
    return filterTest(query, [tenant.name, tenant.alias]);
  });
};

const sortAdministratorTenants = (tenants: Tenant[], order: Order, orderBy: keyof Tenant) => {
  const comparator = getComparator<Tenant>(order, orderBy);
  return [...tenants].sort(comparator);
};

const tableColumns: CustomTableColumn<Tenant>[] = [
  {
    key: "id",
    label: "ID",
    align: "left",
    sortFunction: sortAdministratorTenants,
    render: tenant => {
      return tenant.id;
    },
  },
  {
    key: "name",
    label: "テナント名",
    align: "left",
    sortFunction: sortAdministratorTenants,
    render: tenant => {
      return <Link href={`#/administrator/tenants/${tenant.id}`}>{tenant.name}</Link>;
    },
  },
  {
    key: "alias",
    label: "エイリアス",
    align: "left",
    sortFunction: sortAdministratorTenants,
  },
];

export const TenantsTable = ({ tenants, onDeleteClick }: Props) => {
  const renderActionColumn = (tenant: Tenant) => {
    const isNeoAiTenant = tenant.id === 1;
    return (
      <Stack direction="row" gap={1} justifyContent="right">
        <IconButtonWithTooltip
          onClick={() => onDeleteClick(tenant)}
          color="error"
          tooltipTitle={isNeoAiTenant ? "このテナントは削除できません。" : "削除"}
          disabled={isNeoAiTenant}
          icon={<DeleteOutlineOutlinedIcon />}
        />
      </Stack>
    );
  };

  return (
    <CustomTable<Tenant>
      tableColumns={tableColumns}
      tableData={tenants}
      searchFilter={filterAdministratorTenant}
      renderActionColumn={renderActionColumn}
    />
  );
};
