import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { Box, Container, Stack, Typography } from "@mui/material";
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
import { useDeleteTermsV2, useGetTermsV2 } from "@/orval/backend-api";
import { Bot, DeleteTermsParamV2, TermV2 } from "@/orval/models/backend-api";

import { CreateTermDialog } from "./CreateTermDialog";
import { TermsTable } from "./TermsTable";
import { UpdateTermDialog } from "./UpdateTermDialog";

type Props = {
  selectedBot: Bot;
  hasWritePolicy: boolean;
};

export const TermManagement = ({ selectedBot, hasWritePolicy }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const {
    data: terms,
    isValidating: isGetTermsValidating,
    error: getTermsError,
    mutate: refetchTerms,
  } = useGetTermsV2(selectedBot.id);
  if (getTermsError) {
    const errMsg = getErrorMessage(getTermsError);
    enqueueErrorSnackbar({ message: errMsg || "用語集の取得に失敗しました。" });
  }

  const [selectedRowIds, setSelectedRowIds] = useState<string[]>([]);

  const {
    isOpen: isOpenDeleteTermsDialog,
    open: openDeleteTermsDialog,
    close: closeDeleteTermsDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenCreateTermDialog,
    open: openCreateTermDialog,
    close: closeCreateTermDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenUpdateTermDialog,
    open: openUpdateTermDialog,
    close: closeUpdateTermDialog,
  } = useDisclosure({
    onClose: () => {
      setSelectedTerm(null);
    },
  });

  const [selectedTerm, setSelectedTerm] = useState<TermV2 | null>(null);

  const handleSelectRow = (selectedRowIds: string[]) => {
    setSelectedRowIds(selectedRowIds);
  };

  const handleOpenUpdateDialog = (term: TermV2) => {
    setSelectedTerm(term);
    openUpdateTermDialog();
  };

  const { trigger: deleteTermsTrigger, isMutating: isDeleteTermsMutating } = useDeleteTermsV2(
    selectedBot.id,
  );

  const handleDeleteTerms = async () => {
    try {
      const deleteTerms: DeleteTermsParamV2 = { term_ids: selectedRowIds };
      await deleteTermsTrigger(deleteTerms);
      refetchTerms();
      closeDeleteTermsDialog();
      handleSelectRow([]);
      enqueueSuccessSnackbar({ message: "用語の削除に成功しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "用語の削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Typography>
      <Box component="span" fontWeight="bold">
        {selectedRowIds.length}
      </Box>
      行を削除してもよろしいですか？
    </Typography>
  );

  if (!terms) {
    return (
      <Container sx={{ py: 4 }}>
        <CustomTableSkeleton />
      </Container>
    );
  }

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" flexGrow={1} justifyContent="space-between">
          <Stack direction="row" alignItems="center" gap={0.5}>
            <Typography variant="h4" sx={{ flexGrow: 1 }}>
              用語集
            </Typography>
            <IconButtonWithTooltip
              tooltipTitle="社内の専門用語や略称を登録すると、AIが単語の意味を理解して回答を生成します。"
              color="primary"
              icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
              iconButtonSx={{ p: 0.5 }}
            />
          </Stack>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetchTerms} />
            {hasWritePolicy && (
              <ErrorButton
                text={selectedRowIds.length ? selectedRowIds.length + "行削除" : "削除"}
                onClick={openDeleteTermsDialog}
                disabled={selectedRowIds.length === 0}
              />
            )}
            {hasWritePolicy && (
              <PrimaryButton
                text="追加"
                startIcon={<AddOutlinedIcon />}
                onClick={openCreateTermDialog}
              />
            )}
          </Stack>
        </Stack>
      </ContentHeader>

      <TermsTable
        hasWritePolicy={hasWritePolicy}
        terms={terms?.terms ? terms?.terms : []}
        isLoadingFetchTerms={isGetTermsValidating}
        selectedRowIds={selectedRowIds}
        handleSelectRow={handleSelectRow}
        onClickUpdateIcon={handleOpenUpdateDialog}
      />

      <ConfirmDialog
        open={isOpenDeleteTermsDialog}
        onClose={closeDeleteTermsDialog}
        title="用語削除"
        content={deleteDialogContents}
        buttonText="削除"
        onSubmit={handleDeleteTerms}
        isLoading={isDeleteTermsMutating}
      />

      <CreateTermDialog
        open={isOpenCreateTermDialog}
        onClose={closeCreateTermDialog}
        refetch={refetchTerms}
        botId={selectedBot.id}
      />

      {selectedTerm && (
        <UpdateTermDialog
          open={isOpenUpdateTermDialog}
          onClose={closeUpdateTermDialog}
          term={selectedTerm}
          refetch={refetchTerms}
          assistantId={selectedBot.id}
        />
      )}
    </>
  );
};
