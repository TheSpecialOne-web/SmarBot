import { useState } from "react";

import { Spacer } from "@/components/spacers/Spacer";
import { Tenant } from "@/orval/models/administrator-api";

import { BotsManagement } from "../BotsManagement";
import { TenantSelector } from "../TenantSelector";

type Props = {
  tenants: Tenant[];
};

export const TenantBotsManagement = ({ tenants }: Props) => {
  const [selectedTenant, setSelectedTenant] = useState<Tenant>(tenants[0]);

  const handleSelectTenant = (tenantId: Tenant["id"]) => {
    const selectedTenant = tenants.find(tenant => tenant.id === tenantId);
    if (!selectedTenant) return;
    setSelectedTenant(selectedTenant);
  };
  return (
    <>
      <TenantSelector
        tenants={tenants}
        selectedTenant={selectedTenant}
        onTenantChange={handleSelectTenant}
      />
      <Spacer px={16} />
      <BotsManagement tenant={selectedTenant} />
    </>
  );
};
