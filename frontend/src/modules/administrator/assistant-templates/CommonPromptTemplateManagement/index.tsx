import Add from "@mui/icons-material/Add";
import { Stack, Typography } from "@mui/material";
import { useState } from "react";

import { ErrorButton } from "@/components/buttons/ErrorButton";
import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import {
  useDeleteCommonPromptTemplates,
  useGetCommonPromptTemplates,
} from "@/orval/administrator-api";
import {
  BotTemplate,
  CommonPromptTemplate,
  DeleteCommonPromptTemplateParam,
} from "@/orval/models/administrator-api";

import { CommonPromptTemplatesTable } from "./CommonPromptTemplatesTable";
import { CreateCommonPromptTemplateDialog } from "./CreateCommonPromptTemplateDialog";
import { UpdateCommonPromptTemplateDialog } from "./UpdateCommonPromptTemplateDialog";

type Props = {
  selectedAssistantTemplate: BotTemplate;
};

export const CommonPromptTemplateManagement = ({ selectedAssistantTemplate }: Props) => {
  const [selectedRowIds, setSelectedRowIds] = useState<string[]>([]);
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
      setCommonPromptTemplateToUpdate(null);
    },
  });
  const {
    isOpen: isDeleteDialogOpen,
    open: openDeleteDialog,
    close: closeDeleteDialog,
  } = useDisclosure({});
  const [commonPromptTemplateToUpdate, setCommonPromptTemplateToUpdate] =
    useState<CommonPromptTemplate | null>(null);

  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const {
    data: promptTemplatesData,
    error,
    isLoading: isLoadingGetPromptTemplates,
    mutate: refetchPromptTemplates,
  } = useGetCommonPromptTemplates(selectedAssistantTemplate.id);
  const commonPromptTemplates = promptTemplatesData?.common_prompt_templates ?? [];
  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({ message: errMsg || "質問例の取得に失敗しました。" });
  }

  const { isMutating: loadingDelete, trigger: deleteCommonPromptTemplates } =
    useDeleteCommonPromptTemplates(selectedAssistantTemplate.id);

  const handleOpenUpdateDialog = (promptTemplate: CommonPromptTemplate) => {
    setCommonPromptTemplateToUpdate(promptTemplate);
    openUpdateDialog();
  };

  const handleDeleteCommonPromptTemplates = async () => {
    if (selectedRowIds.length === 0) {
      return;
    }
    try {
      const promptTemplatesToBeDeleted: DeleteCommonPromptTemplateParam = {
        common_prompt_template_ids: selectedRowIds,
      };
      await deleteCommonPromptTemplates(promptTemplatesToBeDeleted);
      enqueueSuccessSnackbar({ message: "質問例を削除しました。" });
      refetchPromptTemplates();
      closeDeleteDialog();
      setSelectedRowIds([]);
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "質問例の削除に失敗しました。",
      });
    }
  };

  if (isLoadingGetPromptTemplates) {
    return <CustomTableSkeleton />;
  }

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">質問例</Typography>
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
      <CommonPromptTemplatesTable
        commonPromptTemplates={commonPromptTemplates}
        selectedRowIds={selectedRowIds}
        handleSelectRow={setSelectedRowIds}
        onClickUpdateIcon={handleOpenUpdateDialog}
      />

      <CreateCommonPromptTemplateDialog
        open={isCreateDialogOpen}
        onClose={closeCreateDialog}
        refetch={refetchPromptTemplates}
        assistantTemplateId={selectedAssistantTemplate.id}
      />

      {commonPromptTemplateToUpdate && (
        <UpdateCommonPromptTemplateDialog
          open={isUpdateDialogOpen}
          onClose={closeUpdateDialog}
          commonPromptTemplate={commonPromptTemplateToUpdate}
          refetch={refetchPromptTemplates}
          assistantTemplateId={selectedAssistantTemplate.id}
        />
      )}

      <ConfirmDialog
        open={isDeleteDialogOpen}
        onClose={closeDeleteDialog}
        title="質問例の削除"
        content={`選択した${selectedRowIds.length}件の質問例を削除してもよろしいですか？`}
        buttonText="削除"
        onSubmit={handleDeleteCommonPromptTemplates}
        isLoading={loadingDelete}
      />
    </>
  );
};
