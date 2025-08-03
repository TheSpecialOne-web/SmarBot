import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import { Box, Container, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { useGetCommonDocumentTemplates } from "@/orval/administrator-api";
import { BotTemplate, CommonDocumentTemplate } from "@/orval/models/administrator-api";

import { CommonDocumentTemplateDataConsolePanel } from "../CommonDocumentTemplateDataConsolePanel";
import { CommonDocumentTemplatesTable } from "../CommonDocumentTemplatesTable";
import { DeleteCommonDocumentTemplateDialog } from "../DeleteCommonDocumentTemplateDialog";
import { UpdateCommonDocumentTemplateDialog } from "../UpdateCommonDocumentTemplateDialog";
import { UploadCommonDocumentTemplateDialog } from "../UploadCommonDocumentTemplateDialog";

type Props = {
  selectedAssistantTemplate: BotTemplate;
};

export const CommonDocumentTemplatesManagement = ({ selectedAssistantTemplate }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const [selectedDocument, setSelectedDocument] = useState<CommonDocumentTemplate | null>();
  const [documentToDisplay, setDocumentToDisplay] = useState<CommonDocumentTemplate>();

  const {
    data: documentsData,
    error: getCommonDocumentTemplatesError,
    isValidating: isGetCommonDocumentTemplateValidating,
    mutate: refetchCommonDocumentTemplates,
  } = useGetCommonDocumentTemplates(selectedAssistantTemplate.id, {
    swr: { enabled: !Number.isNaN(selectedAssistantTemplate.id) },
  });
  if (getCommonDocumentTemplatesError) {
    const errMsg = getErrorMessage(getCommonDocumentTemplatesError);
    enqueueErrorSnackbar({ message: errMsg || "ドキュメントの取得に失敗しました。" });
  }

  const documentTemplates = documentsData?.common_document_templates ?? [];

  const {
    isOpen: isOpenDeleteDocumentDialog,
    open: openDeleteDocumentDialog,
    close: closeDeleteDocumentDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenUpdateDocumentDialog,
    open: openUpdateDocumentDialog,
    close: closeUpdateDocumentDialog,
  } = useDisclosure({
    onClose: () => {
      setSelectedDocument(null);
    },
  });

  const {
    isOpen: isOpenAddDocumentDialog,
    open: openAddDocumentDialog,
    close: closeAddDocumentDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenDocumentDataConsolePanel,
    open: openDocumentDataConsolePanel,
    close: closeDocumentDataConsolePanel,
  } = useDisclosure({});

  const handleOpenDeleteDocumentDialog = (document: CommonDocumentTemplate) => {
    setSelectedDocument(document);
    openDeleteDocumentDialog();
  };

  const handleOpenUpdateDocumentDialog = (document: CommonDocumentTemplate) => {
    setSelectedDocument(document);
    openUpdateDocumentDialog();
  };

  const handleOpenDocumentDataConsolePanel = (document: CommonDocumentTemplate) => {
    setDocumentToDisplay(document);
    openDocumentDataConsolePanel();
  };

  if (isGetCommonDocumentTemplateValidating || !documentsData) {
    return (
      <Container sx={{ py: 4 }}>
        <CustomTableSkeleton />
      </Container>
    );
  }

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" flexGrow={1}>
          <Typography variant="h4" sx={{ flexGrow: 1 }}>
            ドキュメント
          </Typography>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetchCommonDocumentTemplates} />
            <>
              <PrimaryButton
                text={<Typography variant="button">ドキュメント追加</Typography>}
                startIcon={<AddOutlinedIcon />}
                onClick={openAddDocumentDialog}
              />
            </>
          </Stack>
        </Stack>
      </ContentHeader>

      <Box>
        <CommonDocumentTemplatesTable
          documentTemplates={documentTemplates}
          getDocuments={refetchCommonDocumentTemplates}
          onClickDeleteIcon={handleOpenDeleteDocumentDialog}
          onClickUpdateIcon={handleOpenUpdateDocumentDialog}
          onClickDocument={handleOpenDocumentDataConsolePanel}
        />

        <UploadCommonDocumentTemplateDialog
          open={isOpenAddDocumentDialog}
          onClose={closeAddDocumentDialog}
          refetch={refetchCommonDocumentTemplates}
          assistantTemplate={selectedAssistantTemplate}
          documents={documentTemplates}
        />

        {selectedDocument && (
          <DeleteCommonDocumentTemplateDialog
            open={isOpenDeleteDocumentDialog}
            onClose={closeDeleteDocumentDialog}
            document={selectedDocument}
            assistantTemplate={selectedAssistantTemplate}
            refetch={refetchCommonDocumentTemplates}
          />
        )}

        {selectedDocument && (
          <UpdateCommonDocumentTemplateDialog
            open={isOpenUpdateDocumentDialog}
            onClose={closeUpdateDocumentDialog}
            document={selectedDocument}
            assistantTemplate={selectedAssistantTemplate}
            refetch={refetchCommonDocumentTemplates}
          />
        )}

        {documentToDisplay && (
          <CommonDocumentTemplateDataConsolePanel
            isOpen={isOpenDocumentDataConsolePanel}
            onClose={closeDocumentDataConsolePanel}
            document={documentToDisplay}
            botTemplateId={selectedAssistantTemplate.id}
          />
        )}
      </Box>
    </>
  );
};
