import { useLDClient } from "launchdarkly-react-client-sdk";

import { UserTenant } from "@/orval/models/backend-api";

export const useLaunchDarkly = (): {
  updateTenantContext: (tenant: UserTenant | null) => void;
} => {
  const ldClient = useLDClient();

  const updateTenantContext = (tenant: UserTenant | null) => {
    if (!tenant) return;
    ldClient?.identify({
      kind: "tenant",
      key: `tenant_id:${tenant.id}`,
      name: tenant.name,
    });
  };

  return {
    updateTenantContext,
  };
};
