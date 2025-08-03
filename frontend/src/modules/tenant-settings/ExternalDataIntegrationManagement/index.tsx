import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { Paper, Stack, Typography } from "@mui/material";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { useGetTenantExternalDataConnections } from "@/orval/backend-api";
import { ExternalDataConnectionType } from "@/orval/models/backend-api";

import { SharepointIntegration } from "./SharepointIntegration";

type Props = {
  tenantId: number;
};

export const ExternalDataIntegrationManagement = ({ tenantId }: Props) => {
  const { data, mutate: refetchExternalDataConnections } =
    useGetTenantExternalDataConnections(tenantId);
  const sharepointConnection = data?.external_data_connections.find(
    connection =>
      connection.external_data_connection_type === ExternalDataConnectionType.sharepoint,
  );

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" gap={1}>
          <Typography variant="h4">外部データ連携</Typography>
          <IconButtonWithTooltip
            tooltipTitle="外部データ連携のための情報を登録します。連携情報は暗号化されて保存されます。"
            color="primary"
            icon={<HelpOutlineIcon sx={{ fontSize: 18 }} />}
            iconButtonSx={{ p: 0 }}
          />
        </Stack>
      </ContentHeader>
      <Paper
        sx={{
          p: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <SharepointIntegration
          tenantId={tenantId}
          sharepointConnection={sharepointConnection}
          refetchExternalDataConnections={refetchExternalDataConnections}
        />
      </Paper>
    </>
  );
};
