import AddBoxOutlinedIcon from "@mui/icons-material/AddBoxOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import { Button, Stack, Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { sharepointConnectionsInfo } from "@/const/externalDataConnection";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useDeleteExternalDataConnection } from "@/orval/backend-api";
import { ExternalDataConnectionWithHiddenCredentials } from "@/orval/models/backend-api";

import { AddSharepointIntegrationDialog } from "./AddSharepointIntegrationDialog";

type Props = {
  tenantId: number;
  sharepointConnection?: ExternalDataConnectionWithHiddenCredentials;
  refetchExternalDataConnections: () => void;
};

export const SharepointIntegration = ({
  tenantId,
  sharepointConnection,
  refetchExternalDataConnections,
}: Props) => {
  const { isOpen: isOpenAdd, open: openAdd, close: closeAdd } = useDisclosure({});
  const { isOpen: isOpenDelete, open: openDelete, close: closeDelete } = useDisclosure({});

  const { trigger: deleteSharepointIntegration, isMutating: isDeleting } =
    useDeleteExternalDataConnection(tenantId, sharepointConnection?.id ?? "");
  const onConfirmDelete = async () => {
    await deleteSharepointIntegration();
    closeDelete();
    refetchExternalDataConnections();
  };

  return (
    <>
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Typography variant="h5">SharePoint</Typography>
        {sharepointConnection ? (
          <Button
            variant="contained"
            color="error"
            onClick={openDelete}
            startIcon={<DeleteOutlineOutlinedIcon />}
          >
            連携情報を削除
          </Button>
        ) : (
          <Button
            variant="contained"
            color="primary"
            onClick={openAdd}
            startIcon={<AddBoxOutlinedIcon />}
          >
            連携情報を登録
          </Button>
        )}
      </Stack>
      <Stack>
        {sharepointConnection && (
          <>
            <Typography variant="h6">連携情報</Typography>
            <Stack bgcolor="tableBackground.main" p={1.5} borderRadius={1} spacing={0.5}>
              {sharepointConnectionsInfo.map(({ label, key }) => (
                <Stack direction="row" spacing={2} key={key}>
                  <Typography color="text.secondary" width={180}>
                    {label}:
                  </Typography>
                  <Typography>{sharepointConnection.credentials[key]}</Typography>
                </Stack>
              ))}
            </Stack>
          </>
        )}
      </Stack>

      <AddSharepointIntegrationDialog
        tenantId={tenantId}
        isOpen={isOpenAdd}
        close={closeAdd}
        refetchExternalDataConnections={refetchExternalDataConnections}
      />
      <ConfirmDialog
        title="SharePoint連携情報の削除"
        content={
          <Typography>
            SharePoint連携情報を削除してもよろしいですか？
            <br />
            同期中のフォルダがある場合は、速やかに新しい連携情報を入力してください
          </Typography>
        }
        buttonText="削除"
        open={isOpenDelete}
        onClose={closeDelete}
        onSubmit={onConfirmDelete}
        isLoading={isDeleting}
        color="error"
      />
    </>
  );
};
