import Add from "@mui/icons-material/Add";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { Stack, Typography } from "@mui/material";
import { useState } from "react";

import { ErrorButton } from "@/components/buttons/ErrorButton";
import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { useDeleteBotPromptTemplates, useGetBotPromptTemplates } from "@/orval/backend-api";
import { Bot, BotPromptTemplate, DeleteBotPromptTemplatesParam } from "@/orval/models/backend-api";

import { CreatePromptTemplateDialog } from "./CreatePromptTemplateDialog";
import { PromptTemplatesTable } from "./PromptTemplateTable";
import { UpdatePromptTemplateDialog } from "./UpdatePromptTemplateDialog";

type Props = {
  bot: Bot;
  hasWritePolicy: boolean;
};

export const PromptTemplateManagement = ({ bot, hasWritePolicy }: Props) => {
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
      setPromptTemplateToUpdate(null);
    },
  });
  const {
    isOpen: isDeleteDialogOpen,
    open: openDeleteDialog,
    close: closeDeleteDialog,
  } = useDisclosure({});
  const [promptTemplateToUpdate, setPromptTemplateToUpdate] = useState<BotPromptTemplate | null>(
    null,
  );

  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const {
    data: promptTemplatesData,
    error,
    isLoading: isLoadingGetPromptTemplates,
    mutate: refetchPromptTemplates,
  } = useGetBotPromptTemplates(bot.id);
  const promptTemplates = promptTemplatesData?.bot_prompt_templates ?? [];
  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({ message: errMsg || "質問例の取得に失敗しました。" });
  }

  const { isMutating: loadingDelete, trigger: deletePromptTemplates } = useDeleteBotPromptTemplates(
    bot.id,
  );

  const handleOpenUpdateDialog = (promptTemplate: BotPromptTemplate) => {
    setPromptTemplateToUpdate(promptTemplate);
    openUpdateDialog();
  };

  const handleDeletePromptTemplates = async () => {
    if (selectedRowIds.length === 0) {
      return;
    }
    try {
      const promptTemplatesToBeDeleted: DeleteBotPromptTemplatesParam = {
        bot_prompt_template_ids: selectedRowIds,
      };
      await deletePromptTemplates(promptTemplatesToBeDeleted);
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
          <Stack direction="row" alignItems="center" gap={0.5}>
            <Typography variant="h4">質問例</Typography>
            <IconButtonWithTooltip
              tooltipTitle="よく使う質問を設定することで、チャット画面からワンクリックで質問をすることができます。"
              color="primary"
              icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
              iconButtonSx={{ p: 0.5 }}
            />
          </Stack>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetchPromptTemplates} />
            {hasWritePolicy && (
              <>
                <ErrorButton
                  text={selectedRowIds.length ? selectedRowIds.length + "行削除" : "削除"}
                  onClick={openDeleteDialog}
                  disabled={selectedRowIds.length === 0}
                />
                <PrimaryButton startIcon={<Add />} text="追加" onClick={openCreateDialog} />
              </>
            )}
          </Stack>
        </Stack>
      </ContentHeader>
      <PromptTemplatesTable
        promptTemplates={promptTemplates}
        selectedRowIds={selectedRowIds}
        handleSelectRow={setSelectedRowIds}
        onClickUpdateIcon={handleOpenUpdateDialog}
        hasWritePolicy={hasWritePolicy}
      />

      <CreatePromptTemplateDialog
        open={isCreateDialogOpen}
        onClose={closeCreateDialog}
        refetch={refetchPromptTemplates}
        assistantId={bot.id}
      />

      {promptTemplateToUpdate && (
        <UpdatePromptTemplateDialog
          open={isUpdateDialogOpen}
          onClose={closeUpdateDialog}
          promptTemplate={promptTemplateToUpdate}
          refetch={refetchPromptTemplates}
          assistantId={bot.id}
        />
      )}

      <ConfirmDialog
        open={isDeleteDialogOpen}
        onClose={closeDeleteDialog}
        title="質問例の削除"
        content={`選択した${selectedRowIds.length}件の質問例を削除してもよろしいですか？`}
        buttonText="削除"
        onSubmit={handleDeletePromptTemplates}
        isLoading={loadingDelete}
      />
    </>
  );
};
