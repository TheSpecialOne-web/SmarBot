import Add from "@mui/icons-material/Add";
import { Alert, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { ErrorButton } from "@/components/buttons/ErrorButton";
import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { useDeleteApiKeys, useGetApiKeys } from "@/orval/backend-api";
import { ApiKey, DeleteApiKeysParam } from "@/orval/models/backend-api";

import { ApiKeyDetailDialog } from "../ApiKeyDetailDialog";
import { ApiKeysTable } from "../ApiKeysTable";
import { CreateApiKeyDialog } from "../CreateApiKeyDialog";

export const ApiIntegrationManagement = () => {
  const [selectedRowIds, setSelectedRowIds] = useState<string[]>([]);
  const [selectedApiKey, setSelectedApiKey] = useState<ApiKey | null>(null);

  const {
    isOpen: isCreateDialogOpen,
    open: openCreateDialog,
    close: closeCreateDialog,
  } = useDisclosure({});
  const {
    isOpen: isDeleteDialogOpen,
    open: openDeleteDialog,
    close: closeDeleteDialog,
  } = useDisclosure({});
  const {
    isOpen: isApiKeyDetailDialogOpen,
    open: openApiKeyDetailDialog,
    close: closeApiKeyDetailDialog,
  } = useDisclosure({});

  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const {
    data: apiKeysData,
    error,
    isLoading: isLoadingGetApiKeys,
    mutate: refetchApiKeys,
  } = useGetApiKeys();
  const apiKeys = apiKeysData?.api_keys ?? [];
  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({ message: errMsg || "APIキーの取得に失敗しました。" });
  }

  const { isMutating: loadingDelete, trigger: deleteApiKeys } = useDeleteApiKeys();

  const handleDeletePromptTemplates = async () => {
    if (selectedRowIds.length === 0) {
      return;
    }
    try {
      const apiKeysToBeDeleted: DeleteApiKeysParam = {
        api_key_ids: selectedRowIds,
      };
      await deleteApiKeys(apiKeysToBeDeleted);
      enqueueSuccessSnackbar({ message: "APIキーを削除しました。" });
      refetchApiKeys();
      closeDeleteDialog();
      setSelectedRowIds([]);
    } catch (err) {
      enqueueErrorSnackbar({
        message: "APIキーの削除に失敗しました。",
      });
    }
  };

  if (isLoadingGetApiKeys) {
    return <CustomTableSkeleton />;
  }

  return (
    <>
      <Alert severity="warning">
        APIキーを第三者に共有・公開しないでください。APIキーが流出した場合、APIキーを削除し、必要なセキュリティ対策を講じてください。
      </Alert>
      <Spacer px={16} />
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">APIキー</Typography>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetchApiKeys} />
            <ErrorButton
              text={selectedRowIds.length ? selectedRowIds.length + "行削除" : "削除"}
              onClick={openDeleteDialog}
              disabled={selectedRowIds.length === 0}
            />
            <PrimaryButton startIcon={<Add />} text="追加" onClick={openCreateDialog} />
          </Stack>
        </Stack>
      </ContentHeader>
      <ApiKeysTable
        apiKeys={apiKeys}
        selectedRowIds={selectedRowIds}
        handleSelectRow={setSelectedRowIds}
        onClickApiKeyName={apiKey => {
          setSelectedApiKey(apiKey);
          openApiKeyDetailDialog();
        }}
      />

      <CreateApiKeyDialog
        open={isCreateDialogOpen}
        onClose={closeCreateDialog}
        refetch={refetchApiKeys}
      />
      <ConfirmDialog
        open={isDeleteDialogOpen}
        onClose={closeDeleteDialog}
        title="プロンプトテンプレートの削除"
        content={`選択した${selectedRowIds.length}件のAPIキーを削除してもよろしいですか？`}
        buttonText="削除"
        onSubmit={handleDeletePromptTemplates}
        isLoading={loadingDelete}
      />
      {selectedApiKey && (
        <ApiKeyDetailDialog
          isOpen={isApiKeyDetailDialogOpen}
          onClose={closeApiKeyDetailDialog}
          apiKey={selectedApiKey}
        />
      )}
    </>
  );
};
