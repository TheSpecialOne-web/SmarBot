import { Divider, Paper, Stack, Typography } from "@mui/material";

import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useGetTenantStorageUsage, useGetTenantUserCount } from "@/orval/backend-api";
import { Tenant } from "@/orval/models/backend-api";
import { formatBytes } from "@/utils/formatBytes";

import { TenantDashboardItem } from "./TenantDashboardItem";

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
    data: tenantUserCount,
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
    data: tenantStorageUsage,
    mutate: fetchTenantStorageUsage,
  } = useGetTenantStorageUsage(tenant.id, { swr: { enabled: !isLoadingGetTenant } });

  if (errorGetTenantStorageUsage) {
    const errMsg = getErrorMessage(errorGetTenantStorageUsage);
    enqueueErrorSnackbar({
      message: errMsg || "ストレージ使用量の取得に失敗しました",
    });
  }

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">基本情報</Typography>
          <RefreshButton
            onClick={() => {
              refetch();
              fetchTenantUserCount();
              fetchTenantStorageUsage();
            }}
          />
        </Stack>
      </ContentHeader>
      <Paper
        sx={{
          padding: 2,
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
              {`${tenantUserCount?.count} / ${
                tenant?.usage_limit &&
                tenant.usage_limit.free_user_seat + tenant.usage_limit.additional_user_seat
              }`}{" "}
              <Typography fontWeight="bold" component="span">
                人
              </Typography>
            </Typography>
          </TenantDashboardItem>
          <TenantDashboardItem
            title="ストレージ使用量"
            isLoading={isLoadingGetTenant || isLoadingGetTenantStorageUsage}
          >
            <Typography fontWeight="bold">
              {`${tenantStorageUsage?.usage && formatBytes(tenantStorageUsage?.usage)} / ${
                tenant?.usage_limit &&
                formatBytes(tenant.usage_limit.free_storage + tenant.usage_limit.additional_storage)
              }`}
            </Typography>
          </TenantDashboardItem>
        </Stack>
      </Paper>
    </>
  );
};
