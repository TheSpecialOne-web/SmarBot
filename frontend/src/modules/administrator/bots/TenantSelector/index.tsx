import { Autocomplete, FormControl, TextField } from "@mui/material";
import { SyntheticEvent } from "react";

import { Tenant } from "@/orval/models/administrator-api";

type Props = {
  tenants: Tenant[];
  selectedTenant: Tenant;
  onTenantChange: (tenantId: Tenant["id"]) => void;
};

export const TenantSelector = ({ tenants, selectedTenant, onTenantChange }: Props) => {
  const handleChange = (_: SyntheticEvent, value: Tenant | null) => {
    if (!value) return;
    onTenantChange(Number(value.id));
  };

  return (
    <FormControl fullWidth variant="outlined">
      <Autocomplete<Tenant>
        defaultValue={selectedTenant}
        value={selectedTenant}
        onChange={handleChange}
        options={tenants}
        getOptionLabel={option => option.name}
        renderInput={params => <TextField {...params} />}
        sx={{
          maxWidth: "400px",
          backgroundColor: "white",
        }}
      />
    </FormControl>
  );
};
