import AddIcon from "@mui/icons-material/Add";
import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";
import CreateNewFolderOutlinedIcon from "@mui/icons-material/CreateNewFolderOutlined";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAsyncFn } from "react-use";

import { ErrorButton } from "@/components/buttons/ErrorButton";
import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { LoadingDialog } from "@/components/dialogs/LoadingDialog";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { ExpandableMenu } from "@/components/menus/ExpandableMenu";
import { CONVERTIBLE_TO_PDF } from "@/const";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { DataConsolePanel } from "@/modules/assistants/DocumentManagement/DocumentDisplayPanel/DataConsolePanel";
import {
  getDocument,
  getExternalDocumentFolderUrl,
  useDeleteDocuments,
  useGetDocumentFolderDetail,
  useGetDocumentFolders,
  useGetDocuments,
  useGetRootDocumentFolder,
} from "@/orval/backend-api";
import {
  Bot,
  DeleteDocumentsParam,
  Document,
  DocumentFolder,
  ExternalDataConnectionType,
} from "@/orval/models/backend-api";
import { DocumentToDisplay } from "@/types/document";

import { CreateDocumentFolderDialog } from "../CreateDocumentFolderDialog";
import { CreateDocumentFolderFromExternalSourceDialog } from "../CreateDocumentFolderFromExternalSourceDialog";
import { DeleteDocumentDialog } from "../DeleteDocumentDialog";
import { DeleteDocumentFolderDialog } from "../DeleteDocumentFolderDialog";
import { DocumentsTable } from "../DocumentsTable";
import { MoveDocumentDialog } from "../MoveDocumentDialog";
import { MoveDocumentFolderDialog } from "../MoveDocumentFolderDialog";
import { ResyncExternalDocumentFolderDialog } from "../ResyncExternalDocumentFolderDialog";
import { UpdateDocumentDialog } from "../UpdateDocumentDialog";
import { UpdateDocumentFolderDialog } from "../UpdateDocumentFolderDialog";
import { UploadDocumentDialog } from "../UploadDocumentDialog";
import { DocumentFolderBreadcrumbs } from "./DocumentFolderBreadcrumbs";

const SEARCH_PARAM_KEY_FOLDER_ID = "folderId";

type Props = {
  selectedBot: Bot;
  hasWritePolicy: boolean;
};

export const DocumentManagement = ({ selectedBot, hasWritePolicy }: Props) => {
  const [enableDisplayPdf, setEnableDisplayPdf] = useState<boolean>(false);
  const [documentToDisplay, setDocumentToDisplay] = useState<DocumentToDisplay | null>(null);

  const [readPdfError, setPdfError] = useState<boolean>(false);

  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();
  const [selectedDocumentFolder, setSelectedDocumentFolder] = useState<DocumentFolder | null>();
  const [selectedDocument, setSelectedDocument] = useState<Document | null>();
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Document["id"][]>([]);

  const [searchParams, setSearchParams] = useSearchParams();

  const parentDocumentFolderId = searchParams.get(SEARCH_PARAM_KEY_FOLDER_ID) || undefined;

  const {
    data: documentsData,
    error: getDocumentsError,
    isValidating: isGetDocumentValidating,
    mutate: refetchDocuments,
  } = useGetDocuments(
    selectedBot.id,
    { parent_document_folder_id: parentDocumentFolderId },
    {
      swr: {
        enabled: !Number.isNaN(selectedBot.id),
      },
    },
  );
  if (getDocumentsError) {
    const errMsg = getErrorMessage(getDocumentsError);
    enqueueErrorSnackbar({ message: errMsg || "ドキュメントの取得に失敗しました。" });
  }
  const documents = documentsData?.documents ?? [];

  const {
    data: documentFoldersData,
    error: getDocumentFoldersError,
    isValidating: isGetDocumentFoldersValidating,
    mutate: refetchDocumentFolders,
  } = useGetDocumentFolders(
    selectedBot.id,
    { parent_document_folder_id: parentDocumentFolderId },
    {
      swr: {
        enabled: !Number.isNaN(selectedBot.id),
      },
    },
  );
  if (getDocumentFoldersError) {
    const errMsg = getErrorMessage(getDocumentFoldersError);
    enqueueErrorSnackbar({ message: errMsg || "フォルダの取得に失敗しました。" });
  }
  const documentFolders = documentFoldersData?.document_folders ?? [];

  const {
    data: rootDocumentFolderData,
    error: getRootDocumentFolderError,
    isValidating: isGetRootDocumentFolderValidating,
  } = useGetRootDocumentFolder(selectedBot.id);
  if (getRootDocumentFolderError) {
    const errMsg = getErrorMessage(getRootDocumentFolderError);
    enqueueErrorSnackbar({ message: errMsg || "ルートフォルダの取得に失敗しました。" });
  }

  const {
    data: documentFolderDetail,
    error: getDocumentFolderDetailError,
    isValidating: isGetDocumentFolderDetailValidating,
  } = useGetDocumentFolderDetail(
    selectedBot.id,
    parentDocumentFolderId ?? rootDocumentFolderData?.id ?? "",
    {
      swr: {
        enabled: Boolean(parentDocumentFolderId ?? rootDocumentFolderData?.id),
      },
    },
  );
  if (getDocumentFolderDetailError) {
    const errMsg = getErrorMessage(getDocumentFolderDetailError);
    enqueueErrorSnackbar({ message: errMsg || "フォルダ詳細の取得に失敗しました。" });
  }

  const refetchDocumentsAndDocumentFolders = async () => {
    await Promise.all([refetchDocuments(), refetchDocumentFolders()]);
  };

  const {
    isOpen: isOpenDeleteDocumentFolderDialog,
    open: openDeleteDocumentFolderDialog,
    close: closeDeleteDocumentFolderDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenMoveDocumentFolderDialog,
    open: openMoveDocumentFolderDialog,
    close: closeMoveDocumentFolderDialog,
  } = useDisclosure({
    onClose: () => {
      setSelectedDocumentFolder(null);
    },
  });

  const {
    isOpen: isOpenUpdateDocumentFolderDialog,
    open: openUpdateDocumentFolderDialog,
    close: closeUpdateDocumentFolderDialog,
  } = useDisclosure({
    onClose: () => {
      setSelectedDocumentFolder(null);
    },
  });

  const {
    isOpen: isOpenResyncExternalDocumentFolderDialog,
    open: openResyncExternalDocumentFolderDialog,
    close: closeResyncExternalDocumentFolderDialog,
  } = useDisclosure({
    onClose: () => {
      setSelectedDocumentFolder(null);
    },
  });

  const {
    isOpen: isOpenDeleteExternalDocumentFolderDialog,
    open: openDeleteExternalDocumentFolderDialog,
    close: closeDeleteExternalDocumentFolderDialog,
  } = useDisclosure({
    onClose: () => {
      setSelectedDocumentFolder(null);
    },
  });

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
    isOpen: isOpenMoveDocumentDialog,
    open: openMoveDocumentDialog,
    close: closeMoveDocumentDialog,
  } = useDisclosure({
    onClose: () => {
      setSelectedDocument(null);
    },
  });

  const {
    isOpen: isOpenDeleteDocumentsDialog,
    open: openDeleteDocumentsDialog,
    close: closeDeleteDocumentsDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenAddDocumentDialog,
    open: openAddDocumentDialog,
    close: closeAddDocumentDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenCreateDocumentFolderDialog,
    open: openCreateDocumentFolderDialog,
    close: closeCreateDocumentFolderDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenCreateDocumentFolderFromExternalSourceDialog,
    open: openCreateDocumentFolderFromExternalSourceDialog,
    close: closeCreateDocumentFolderFromExternalSourceDialog,
  } = useDisclosure({});

  const handleSelectRow = (selectedDocumentIds: number[]) => {
    setSelectedDocumentIds(selectedDocumentIds);
  };

  const { trigger: deleteDocumentsTrigger, isMutating: isDeleteDocumentsMutating } =
    useDeleteDocuments(selectedBot.id);

  const handleDeleteDocuments = async () => {
    try {
      const deleteDocuments: DeleteDocumentsParam = { document_ids: selectedDocumentIds };
      await deleteDocumentsTrigger(deleteDocuments);
      refetchDocuments();
      closeDeleteDocumentsDialog();
      handleSelectRow([]);
      enqueueSuccessSnackbar({
        message: "ドキュメントの削除を開始しました。",
      });
    } catch (err) {
      const errMsg = getErrorMessage(err);
      enqueueErrorSnackbar({ message: errMsg || "ドキュメントの削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Stack gap={2}>
      <Typography variant="body1">以下のドキュメントを削除してもよろしいですか？</Typography>
      <List
        sx={{
          width: "100%",
          maxWidth: 400,
          maxHeight: 300,
          overflow: "auto",
          bgcolor: "primaryBackground.main",
        }}
      >
        {selectedDocumentIds.map(id => {
          const document = documents.find(document => document.id === id);
          if (!document) return null;
          return (
            <ListItem key={id}>
              <ListItemText>
                ・{document.name}.{document.file_extension}
              </ListItemText>
            </ListItem>
          );
        })}
      </List>
      <Typography variant="caption">
        ※ドキュメントの削除には時間がかかる場合があります。
        <br />
        削除が完了すると表示されなくなります。
      </Typography>
    </Stack>
  );

  const handleOpenDeleteDocumentDialog = (document: Document) => {
    setSelectedDocument(document);
    openDeleteDocumentDialog();
  };

  const handleOpenUpdateDocumentDialog = (document: Document) => {
    setSelectedDocument(document);
    openUpdateDocumentDialog();
  };

  const handleOpenMoveDocumentDialog = (document: Document) => {
    setSelectedDocument(document);
    openMoveDocumentDialog();
  };

  const handleOpenDeleteDocumentFolderDialog = (documentFolder: DocumentFolder) => {
    setSelectedDocumentFolder(documentFolder);
    openDeleteDocumentFolderDialog();
  };

  const handleOpenMoveDocumentFolderDialog = (documentFolder: DocumentFolder) => {
    setSelectedDocumentFolder(documentFolder);
    openMoveDocumentFolderDialog();
  };

  const handleOpenUpdateDocumentFolderDialog = (documentFolder: DocumentFolder) => {
    setSelectedDocumentFolder(documentFolder);
    openUpdateDocumentFolderDialog();
  };

  const handleOpenResyncExternalDocumentFolderDialog = (documentFolder: DocumentFolder) => {
    setSelectedDocumentFolder(documentFolder);
    openResyncExternalDocumentFolderDialog();
  };

  const handleOpenDeleteExternalDocumentFolderDialog = (documentFolder: DocumentFolder) => {
    setSelectedDocumentFolder(documentFolder);
    openDeleteExternalDocumentFolderDialog();
  };

  // PDFの表示を消す関数
  const handleClearPdfData = () => {
    setEnableDisplayPdf(false);
    setDocumentToDisplay(null);
    setPdfError(false);
  };

  // PDFの名前をクリックした時に呼ばれる関数
  const [handleOpenPdfState, handleOpenPdf] = useAsyncFn(async (document: Document) => {
    try {
      setEnableDisplayPdf(true);
      const documentDetail = await getDocument(selectedBot.id, document.id);
      setDocumentToDisplay({
        name: documentDetail.name,
        extension: documentDetail.file_extension,
        displayUrl: CONVERTIBLE_TO_PDF.includes(documentDetail.file_extension)
          ? documentDetail.signed_url_pdf || ""
          : documentDetail.signed_url_original,
        downloadUrl: documentDetail.signed_url_original,
        documentFolderDetail: documentDetail.parent_document_folder,
      });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      setPdfError(true);
      enqueueErrorSnackbar({ message: errMsg || "PDFの表示に失敗しました。" });
    }
  });

  const onMoveToFolder = async (folderId: string | null) => {
    // フォルダIDが指定されている場合は、URLパラメータに追加→特定のフォルダに移動
    if (folderId) {
      const currentParams = Object.fromEntries(searchParams);
      setSearchParams({
        ...currentParams,
        folderId,
      });
      return;
    }

    // フォルダIDが指定されていない場合は、URLパラメータから削除→ルートフォルダに移動
    if (searchParams.has(SEARCH_PARAM_KEY_FOLDER_ID)) {
      searchParams.delete(SEARCH_PARAM_KEY_FOLDER_ID);
      setSearchParams(searchParams);
    }
  };

  const [onMoveToExternalDocumentFolderState, onMoveToExternalDocumentFolder] = useAsyncFn(
    async (folderId: string, externalType: ExternalDataConnectionType) => {
      try {
        const externalUrl = await getExternalDocumentFolderUrl(selectedBot.id, folderId, {
          external_data_connection_type: externalType,
        });
        window.open(externalUrl.url, "_blank");
      } catch (e) {
        const errMsg = getErrorMessage(e);
        enqueueErrorSnackbar({ message: errMsg || "外部フォルダの取得に失敗しました。" });
      }
    },
  );

  const isLoading =
    isGetDocumentValidating ||
    isGetDocumentFoldersValidating ||
    isGetRootDocumentFolderValidating ||
    isGetDocumentFolderDetailValidating;

  return (
    <>
      {!isGetRootDocumentFolderValidating && !isGetDocumentFolderDetailValidating && (
        <ContentHeader>
          <Stack direction="row" alignItems="center" flexGrow={1} justifyContent="space-between">
            <Stack direction="row" alignItems="center" gap={1}>
              <Stack direction="row" alignItems="center" gap={0.5}>
                <Typography variant="h4" sx={{ flexGrow: 1 }}>
                  ドキュメント
                </Typography>
                <IconButtonWithTooltip
                  tooltipTitle="AIに学習させる企業データです。登録されたドキュメントをもとに生成AIが回答します。"
                  color="primary"
                  icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
                  iconButtonSx={{ p: 0.5 }}
                />
              </Stack>
              {documentFolderDetail && rootDocumentFolderData && (
                <DocumentFolderBreadcrumbs
                  documentFolderDetail={documentFolderDetail}
                  rootDocumentFolderId={rootDocumentFolderData.id}
                  onMoveToFolder={onMoveToFolder}
                />
              )}
            </Stack>
            <Stack direction="row" gap={2}>
              <RefreshButton onClick={refetchDocumentsAndDocumentFolders} />
              {hasWritePolicy && (
                <>
                  <ErrorButton
                    text={
                      selectedDocumentIds.length ? selectedDocumentIds.length + "行削除" : "削除"
                    }
                    onClick={openDeleteDocumentsDialog}
                    disabled={selectedDocumentIds.length === 0}
                  />
                  <ExpandableMenu title="新規追加" startIcon={<AddIcon />}>
                    <MenuItem onClick={openCreateDocumentFolderDialog}>
                      <ListItemIcon>
                        <CreateNewFolderOutlinedIcon />
                      </ListItemIcon>
                      <ListItemText>新しいフォルダ</ListItemText>
                    </MenuItem>
                    <MenuItem onClick={openAddDocumentDialog}>
                      <ListItemIcon>
                        <UploadFileIcon />
                      </ListItemIcon>
                      <ListItemText>ドキュメントアップロード</ListItemText>
                    </MenuItem>
                    <MenuItem onClick={openCreateDocumentFolderFromExternalSourceDialog}>
                      <ListItemIcon>
                        <CloudUploadOutlinedIcon />
                      </ListItemIcon>
                      <ListItemText>外部ソースからフォルダを追加</ListItemText>
                    </MenuItem>
                  </ExpandableMenu>
                </>
              )}
            </Stack>
          </Stack>
        </ContentHeader>
      )}

      <Box>
        <DocumentsTable
          documents={documents}
          documentFolders={documentFolders}
          onMoveToFolder={onMoveToFolder}
          handleOpenPdf={handleOpenPdf}
          hasWritePolicy={hasWritePolicy}
          onClickUpdateDocumentFolderIcon={handleOpenUpdateDocumentFolderDialog}
          onClickDeleteDocumentFolderIcon={handleOpenDeleteDocumentFolderDialog}
          onClickMoveDocumentFolderIcon={handleOpenMoveDocumentFolderDialog}
          onClickResyncExternalDocumentFolderIcon={handleOpenResyncExternalDocumentFolderDialog}
          onClickDeleteExternalDocumentFolderIcon={handleOpenDeleteExternalDocumentFolderDialog}
          onClickUpdateDocumentIcon={handleOpenUpdateDocumentDialog}
          onClickDeleteDocumentIcon={handleOpenDeleteDocumentDialog}
          onClickMoveDocumentIcon={handleOpenMoveDocumentDialog}
          onClickExternalDocumentFolder={onMoveToExternalDocumentFolder}
          selectedRowIds={selectedDocumentIds}
          handleSelectRow={handleSelectRow}
          isLoading={isLoading}
        />

        <DataConsolePanel
          open={enableDisplayPdf}
          onClose={handleClearPdfData}
          isLoading={handleOpenPdfState.loading}
          documentToDisplay={documentToDisplay}
          readPdfError={readPdfError}
        />

        <ConfirmDialog
          open={isOpenDeleteDocumentsDialog}
          onClose={closeDeleteDocumentsDialog}
          title="ドキュメント削除"
          content={deleteDialogContents}
          buttonText="削除"
          onSubmit={handleDeleteDocuments}
          isLoading={isDeleteDocumentsMutating}
        />

        <CreateDocumentFolderDialog
          open={isOpenCreateDocumentFolderDialog}
          onClose={closeCreateDocumentFolderDialog}
          bot={selectedBot}
          parentDocumentFolderId={parentDocumentFolderId || null}
          refetch={refetchDocumentsAndDocumentFolders}
        />

        <UploadDocumentDialog
          open={isOpenAddDocumentDialog}
          onClose={closeAddDocumentDialog}
          refetch={refetchDocumentsAndDocumentFolders}
          bot={selectedBot}
          parentDocumentFolderId={parentDocumentFolderId || null}
          documents={documents}
        />

        <LoadingDialog open={onMoveToExternalDocumentFolderState.loading} />

        <CreateDocumentFolderFromExternalSourceDialog
          botId={selectedBot.id}
          open={isOpenCreateDocumentFolderFromExternalSourceDialog}
          onClose={closeCreateDocumentFolderFromExternalSourceDialog}
          parentDocumentFolderId={parentDocumentFolderId || null}
          refetch={refetchDocumentsAndDocumentFolders}
        />

        {selectedDocumentFolder && (
          <DeleteDocumentFolderDialog
            open={isOpenDeleteDocumentFolderDialog}
            onClose={closeDeleteDocumentFolderDialog}
            documentFolder={selectedDocumentFolder}
            bot={selectedBot}
            refetch={refetchDocumentFolders}
          />
        )}
        {selectedDocumentFolder && rootDocumentFolderData && documentFolderDetail && (
          <MoveDocumentFolderDialog
            bot={selectedBot}
            open={isOpenMoveDocumentFolderDialog}
            targetDocumentFolder={selectedDocumentFolder}
            rootDocumentFolder={rootDocumentFolderData}
            currentParentDocumentFolderDetail={documentFolderDetail}
            refetch={refetchDocumentFolders}
            onClose={closeMoveDocumentFolderDialog}
          />
        )}
        {selectedDocumentFolder && (
          <UpdateDocumentFolderDialog
            open={isOpenUpdateDocumentFolderDialog}
            onClose={closeUpdateDocumentFolderDialog}
            documentFolder={selectedDocumentFolder}
            bot={selectedBot}
            refetch={refetchDocumentFolders}
          />
        )}

        {selectedDocumentFolder && (
          <ResyncExternalDocumentFolderDialog
            open={isOpenResyncExternalDocumentFolderDialog}
            documentFolder={selectedDocumentFolder}
            bot={selectedBot}
            onClose={closeResyncExternalDocumentFolderDialog}
            refetch={refetchDocumentFolders}
          />
        )}
        {selectedDocumentFolder && (
          <DeleteDocumentFolderDialog
            open={isOpenDeleteExternalDocumentFolderDialog}
            onClose={closeDeleteExternalDocumentFolderDialog}
            documentFolder={selectedDocumentFolder}
            bot={selectedBot}
            refetch={refetchDocumentFolders}
            isExternal
          />
        )}

        {selectedDocument && (
          <DeleteDocumentDialog
            open={isOpenDeleteDocumentDialog}
            onClose={closeDeleteDocumentDialog}
            document={selectedDocument}
            bot={selectedBot}
            refetch={refetchDocumentsAndDocumentFolders}
          />
        )}
        {selectedDocument && (
          <UpdateDocumentDialog
            open={isOpenUpdateDocumentDialog}
            onClose={closeUpdateDocumentDialog}
            document={selectedDocument}
            bot={selectedBot}
            refetch={refetchDocumentsAndDocumentFolders}
          />
        )}
        {selectedDocument && rootDocumentFolderData && documentFolderDetail && (
          <MoveDocumentDialog
            bot={selectedBot}
            open={isOpenMoveDocumentDialog}
            targetDocument={selectedDocument}
            rootDocumentFolder={rootDocumentFolderData}
            currentDocumentFolderDetail={documentFolderDetail}
            refetch={refetchDocumentsAndDocumentFolders}
            onClose={closeMoveDocumentDialog}
          />
        )}
      </Box>
    </>
  );
};
