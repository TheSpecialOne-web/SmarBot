import { Spacer } from "@/components/spacers/Spacer";
import { Tenant } from "@/orval/models/administrator-api";

import { DocumentIntelligenceConsumption } from "./DocumentIntelligenceConsumption";
import { TenantDashboard } from "./TenantDashboard";
import { TokenConsumption } from "./TokenConsumption";

type Props = {
  tenant: Tenant;
  isLoading: boolean;
  refetchTenant: () => void;
};

export const Statistics = ({ tenant, isLoading, refetchTenant }: Props) => {
  return (
    <>
      <TenantDashboard tenant={tenant} refetch={refetchTenant} isLoadingGetTenant={isLoading} />
      <Spacer px={16} />
      <TokenConsumption tenant={tenant} isLoadingGetTenant={isLoading} />
      <Spacer px={16} />
      <DocumentIntelligenceConsumption tenant={tenant} isLoadingGetTenant={isLoading} />
    </>
  );
};
