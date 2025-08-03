import { Divider, Paper, Stack, Typography } from "@mui/material";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { UpdateUsageLimitDialog } from "@/modules/administrator/tenants/UpdateUsageLimitDialog";
import { useGetTenantStorageUsage, useGetTenantUserCount } from "@/orval/administrator-api";
import { Tenant } from "@/orval/models/administrator-api";
import { formatBytes } from "@/utils/formatBytes";

import { TenantDashboardItem } from "./Item";

type Props = {
  tenant: Tenant;
  refetch: () => void;
  isLoadingGetTenant: boolean;
};

export const TenantDashboard = ({ tenant, refetch, isLoadingGetTenant }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const {
    isValidating: isLoadingGetTenantUserCount,
    error: errorGetTenantUserCount,
    data: tenantUserCountData,
    mutate: fetchTenantUserCount,
  } = useGetTenantUserCount(tenant.id, { swr: { enabled: !isLoadingGetTenant } });

  if (errorGetTenantUserCount) {
    const errMsg = getErrorMessage(errorGetTenantUserCount);
    enqueueErrorSnackbar({
      message: errMsg || "ユーザー数の取得に失敗しました",
    });
  }

  const {
    isValidating: isLoadingGetTenantStorageUsage,
    error: errorGetTenantStorageUsage,
    data: tenantStorageUsageData,
    mutate: fetchTenantStorageUsage,
  } = useGetTenantStorageUsage(tenant.id, { swr: { enabled: !isLoadingGetTenant } });

  if (errorGetTenantStorageUsage) {
    const errMsg = getErrorMessage(errorGetTenantStorageUsage);
    enqueueErrorSnackbar({
      message: errMsg || "ストレージ使用量の取得に失敗しました",
    });
  }

  const freeUserSeat = tenant.usage_limit.free_user_seat;
  const additionalUserSeat = tenant.usage_limit.additional_user_seat;
  const freeStorageLimit = formatBytes(tenant.usage_limit.free_storage);
  const additionalStorageLimit =
    tenant.usage_limit.additional_storage == 0
      ? "0 GB"
      : formatBytes(tenant.usage_limit.additional_storage);
  const totalUserSeat = freeUserSeat + additionalUserSeat;
  const totalStorageLimit = formatBytes(
    tenant.usage_limit.free_storage + tenant.usage_limit.additional_storage,
  );

  const tenantUserCount = tenantUserCountData?.count ?? 0;

  const storageUsage = formatBytes(tenantStorageUsageData?.usage ?? 0);

  const {
    isOpen: isOpenUpdateTenantDialog,
    open: openUpdateTenantDialog,
    close: closeUpdateTenantDialog,
  } = useDisclosure({});

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">基本情報</Typography>
          <Stack direction="row" gap={2}>
            <PrimaryButton text="編集" onClick={openUpdateTenantDialog} />
            <RefreshButton
              onClick={() => {
                refetch();
                fetchTenantUserCount();
                fetchTenantStorageUsage();
              }}
            />
          </Stack>
        </Stack>
      </ContentHeader>
      <Paper
        sx={{
          p: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-evenly"
          divider={<Divider orientation="vertical" flexItem />}
        >
          <TenantDashboardItem
            title="ユーザー数"
            isLoading={isLoadingGetTenant || isLoadingGetTenantUserCount}
          >
            <Typography fontWeight="bold">
              {`${tenantUserCount} / ${totalUserSeat}`}
              <Typography component="span" fontSize="small" fontWeight="bold">
                人
              </Typography>
            </Typography>
            <Typography>
              (無料枠: {freeUserSeat} + 追加購入: {additionalUserSeat})
            </Typography>
          </TenantDashboardItem>
          <TenantDashboardItem
            title="ストレージ使用量"
            isLoading={isLoadingGetTenant || isLoadingGetTenantStorageUsage}
          >
            <Typography fontWeight="bold">{`${storageUsage} / ${totalStorageLimit}`}</Typography>
            <Typography>
              (無料枠: {freeStorageLimit} + 追加購入: {additionalStorageLimit})
            </Typography>
          </TenantDashboardItem>
        </Stack>
      </Paper>
      <UpdateUsageLimitDialog
        tenant={tenant}
        open={isOpenUpdateTenantDialog}
        onClose={closeUpdateTenantDialog}
        refetch={refetch}
      />
    </>
  );
};
