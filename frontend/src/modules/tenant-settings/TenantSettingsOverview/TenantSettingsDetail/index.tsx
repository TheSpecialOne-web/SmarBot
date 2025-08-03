import { Divider, Paper, Stack, Typography } from "@mui/material";

import { ContentHeader } from "@/components/headers/ContentHeader";
import { Tenant } from "@/orval/models/backend-api";

import { ForeignRegionManagement } from "./ForeignRegionManagement";
import { MaxAttachmentTokenManagement } from "./MaxAttachmentTokenManagement";
import { PersonalInfoManagement } from "./PersonalInfoManagement";
import { PlatformManagement } from "./PlatformManagement";

type Props = {
  tenant: Tenant;
  refetch: () => void;
  isLoadingGetTenant: boolean;
};

export const TenantSettingsDetail = ({ tenant, refetch, isLoadingGetTenant }: Props) => {
  return (
    <>
      <ContentHeader>
        <Typography variant="h3">組織の設定</Typography>
      </ContentHeader>
      <Paper
        sx={{
          padding: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <Stack divider={<Divider />} spacing={2}>
          <MaxAttachmentTokenManagement
            tenant={tenant}
            refetch={refetch}
            isLoadingGetTenant={isLoadingGetTenant}
          />
          <PersonalInfoManagement
            tenant={tenant}
            refetch={refetch}
            isLoadingGetTenant={isLoadingGetTenant}
          />
          <ForeignRegionManagement tenant={tenant} isLoadingGetTenant={isLoadingGetTenant} />
          <PlatformManagement
            additionalPlatforms={tenant.additional_platforms}
            isLoadingGetTenant={isLoadingGetTenant}
          />
        </Stack>
      </Paper>
    </>
  );
};
