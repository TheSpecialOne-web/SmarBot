import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useGetTenant } from "@/orval/backend-api";
import { UserTenant } from "@/orval/models/backend-api";

import { DocumentIntelligenceConsumption } from "../TenantSettingsOverview/DocumentIntelligenceConsumption";
import { TenantDashboard } from "../TenantSettingsOverview/TenantDashboard";
import { TokenConsumption } from "../TenantSettingsOverview/TokenConsumption";

type Props = {
  tenant: UserTenant;
};

export const UsageManagement = ({ tenant }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const {
    isValidating: isLoadingGetTenant,
    error,
    data: tenantDetail,
    mutate: refetchTenant,
  } = useGetTenant(tenant.id);

  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({
      message: errMsg || "組織の情報の取得に失敗しました",
    });
  }
  return (
    <>
      {tenantDetail && (
        <TenantDashboard
          tenant={tenantDetail}
          refetch={refetchTenant}
          isLoadingGetTenant={isLoadingGetTenant}
        />
      )}
      <Spacer px={16} />
      {tenantDetail && (
        <TokenConsumption tenant={tenantDetail} isLoadingGetTenant={isLoadingGetTenant} />
      )}
      <Spacer px={16} />

      {tenant.enable_document_intelligence && tenantDetail && (
        <DocumentIntelligenceConsumption
          tenant={tenantDetail}
          isLoadingGetTenant={isLoadingGetTenant}
        />
      )}
    </>
  );
};
