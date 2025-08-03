import Add from "@mui/icons-material/Add";
import { Stack, Typography } from "@mui/material";
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
import { useDeletePromptTemplates, useGetPromptTemplates } from "@/orval/backend-api";
import { DeletePromptTemplatesParam, PromptTemplate, UserTenant } from "@/orval/models/backend-api";

import { CreatePromptTemplateDialog } from "../CreatePromptTemplateDialog";
import { PromptTemplatesTable } from "../PromptTemplatesTable";
import { UpdatePromptTemplateDialog } from "../UpdatePromptTemplateDialog";
import { BasicAiSettings } from "./BasicAiSettings";

type Props = {
  tenant: UserTenant;
};

export const BasicAiManagement = ({ tenant }: Props) => {
  const [selectedRowIds, setSelectedRowIds] = useState<number[]>([]);
  const {
    isOpen: isCreateDialogOpen,
    open: openCreateDialog,
    close: closeCreateDialog,
  } = useDisclosure({});
  const {
    isOpen: isUpdateDialogOpen,
    open: openUpdateDialog,
    close: closeUpdateDialog,
  } = useDisclosure({
    onClose: () => {
      setPromptTemplateToUpdate(null);
    },
  });
  const {
    isOpen: isDeleteDialogOpen,
    open: openDeleteDialog,
    close: closeDeleteDialog,
  } = useDisclosure({});
  const [promptTemplateToUpdate, setPromptTemplateToUpdate] = useState<PromptTemplate | null>(null);

  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const {
    data: promptTemplatesData,
    error,
    isLoading: isLoadingGetPromptTemplates,
    mutate: refetchPromptTemplates,
  } = useGetPromptTemplates();
  const promptTemplates = promptTemplatesData?.prompt_templates ?? [];
  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({ message: errMsg || "プロンプトテンプレートの取得に失敗しました。" });
  }

  const { isMutating: loadingDelete, trigger: deletePromptTemplates } = useDeletePromptTemplates();

  const handleOpenUpdateDialog = (promptTemplate: PromptTemplate) => {
    setPromptTemplateToUpdate(promptTemplate);
    openUpdateDialog();
  };

  const handleDeletePromptTemplates = async () => {
    if (selectedRowIds.length === 0) {
      return;
    }
    try {
      const promptTemplatesToBeDeleted: DeletePromptTemplatesParam = {
        prompt_template_ids: selectedRowIds,
      };
      await deletePromptTemplates(promptTemplatesToBeDeleted);
      enqueueSuccessSnackbar({ message: "プロンプトテンプレートを削除しました。" });
      refetchPromptTemplates();
      closeDeleteDialog();
      setSelectedRowIds([]);
    } catch (err) {
      enqueueErrorSnackbar({
        message: "プロンプトテンプレートの削除に失敗しました。",
      });
    }
  };

  if (isLoadingGetPromptTemplates) {
    return <CustomTableSkeleton />;
  }

  return (
    <>
      <BasicAiSettings tenant={tenant} />
      <Spacer px={16} />
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">プロンプトテンプレート</Typography>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetchPromptTemplates} />
            <ErrorButton
              text={selectedRowIds.length ? selectedRowIds.length + "行削除" : "削除"}
              onClick={openDeleteDialog}
              disabled={selectedRowIds.length === 0}
            />
            <PrimaryButton startIcon={<Add />} text="追加" onClick={openCreateDialog} />
          </Stack>
        </Stack>
      </ContentHeader>
      <PromptTemplatesTable
        promptTemplates={promptTemplates}
        selectedRowIds={selectedRowIds}
        handleSelectRow={setSelectedRowIds}
        onClickUpdateIcon={handleOpenUpdateDialog}
      />

      <CreatePromptTemplateDialog
        open={isCreateDialogOpen}
        onClose={closeCreateDialog}
        refetch={refetchPromptTemplates}
      />
      {promptTemplateToUpdate && (
        <UpdatePromptTemplateDialog
          open={isUpdateDialogOpen}
          onClose={closeUpdateDialog}
          promptTemplate={promptTemplateToUpdate}
          refetch={refetchPromptTemplates}
        />
      )}
      <ConfirmDialog
        open={isDeleteDialogOpen}
        onClose={closeDeleteDialog}
        title="プロンプトテンプレートの削除"
        content={`選択した${selectedRowIds.length}件のプロンプトテンプレートを削除してもよろしいですか？`}
        buttonText="削除"
        onSubmit={handleDeletePromptTemplates}
        isLoading={loadingDelete}
      />
    </>
  );
};
