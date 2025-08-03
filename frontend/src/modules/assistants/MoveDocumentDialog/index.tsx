import { Typography } from "@mui/material";
import { useState } from "react";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import {
  useGetDocumentFolderDetail,
  useGetDocumentFolders,
  useGetDocuments,
} from "@/orval/backend-api";
import {
  Bot,
  Document,
  DocumentFolder,
  DocumentFolderDetail,
  MoveDocumentParam,
} from "@/orval/models/backend-api";

import { ConfirmMoveDocumentDialog } from "../ConfirmMoveDocumentDialog";
import { MoveDocumentTable } from "./MoveDocumentTable";

type Props = {
  bot: Bot;
  open: boolean;
  targetDocument: Document;
  rootDocumentFolder: DocumentFolder;
  currentDocumentFolderDetail: DocumentFolderDetail;
  onClose: () => void;
  refetch: () => void;
};

export const MoveDocumentDialog = ({
  bot,
  open,
  targetDocument,
  rootDocumentFolder,
  currentDocumentFolderDetail,
  onClose,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const [displayedDocumentFolderId, setDisplayedDocumentFolderId] = useState<string>(
    currentDocumentFolderDetail.id ?? rootDocumentFolder.id,
  );

  const [newParentDocumentFolderId, setNewParentDocumentFolderId] = useState<string | null>(null);

  const {
    isOpen: isOpenConfirmMoveDocumentDialog,
    open: openConfirmMoveDocumentDialog,
    close: closeConfirmMoveDocumentDialog,
  } = useDisclosure({
    onClose: () => {
      setNewParentDocumentFolderId(null);
    },
  });

  const handleOpenConfirmMoveDocumentDialog = (param: MoveDocumentParam) => {
    setNewParentDocumentFolderId(param.document_folder_id);
    openConfirmMoveDocumentDialog();
  };

  const {
    data: documentsData,
    error: getDocumentsError,
    isValidating: isValidatingGetDocument,
  } = useGetDocuments(bot.id, { parent_document_folder_id: displayedDocumentFolderId });
  if (getDocumentsError) {
    const errMsg = getErrorMessage(getDocumentsError);
    enqueueErrorSnackbar({ message: errMsg || "ドキュメントの取得に失敗しました。" });
  }
  const documents = documentsData?.documents ?? [];

  const {
    data: documentFoldersData,
    error: getDocumentFoldersError,
    isValidating: isValidatingGetDocumentFolders,
  } = useGetDocumentFolders(bot.id, { parent_document_folder_id: displayedDocumentFolderId });
  if (getDocumentFoldersError) {
    const errMsg = getErrorMessage(getDocumentFoldersError);
    enqueueErrorSnackbar({ message: errMsg || "フォルダの取得に失敗しました。" });
  }
  const documentFolders = documentFoldersData?.document_folders ?? [];

  const {
    data: displayedDocumentFolderDetail,
    error: getDisplayedDocumentFolderDetailError,
    isValidating: isValidatingGetDisplayedDocumentFolderDetail,
  } = useGetDocumentFolderDetail(bot.id, displayedDocumentFolderId, {
    swr: {
      // newParentDocumentFolderDetail の useGetDocumentFolderDetail と区別するためのキー
      swrKey: ["displayedDocumentFolderDetail", bot.id, displayedDocumentFolderId],
    },
  });
  if (getDisplayedDocumentFolderDetailError) {
    const errMsg = getErrorMessage(getDisplayedDocumentFolderDetailError);
    enqueueErrorSnackbar({ message: errMsg || "フォルダ詳細の取得に失敗しました。" });
  }

  const {
    data: newParentDocumentFolderDetail,
    error: getNewParentDocumentFolderDetailError,
    isValidating: isValidatingGetNewParentDocumentFolderDetail,
  } = useGetDocumentFolderDetail(bot.id, newParentDocumentFolderId ?? "", {
    swr: {
      enabled: Boolean(newParentDocumentFolderId),
    },
  });
  if (getNewParentDocumentFolderDetailError) {
    const errMsg = getErrorMessage(getNewParentDocumentFolderDetailError);
    enqueueErrorSnackbar({ message: errMsg || "フォルダ詳細の取得に失敗しました。" });
  }

  const handleMoveToFolder = (folderId: string) => {
    setDisplayedDocumentFolderId(folderId);
  };

  return (
    <>
      <CustomDialog
        open={open}
        title={
          <Typography variant="h4" sx={{ flexGrow: 1 }}>
            {targetDocument.name} を移動
          </Typography>
        }
        maxWidth="md"
        onClose={onClose}
      >
        <MoveDocumentTable
          rootDocumentFolder={rootDocumentFolder}
          documents={documents}
          documentFolders={documentFolders}
          displayedDocumentFolderDetail={displayedDocumentFolderDetail}
          currentParentDocumentFolderDetail={currentDocumentFolderDetail}
          onMoveToFolder={handleMoveToFolder}
          onSubmit={handleOpenConfirmMoveDocumentDialog}
          onClose={onClose}
          isLoading={
            isValidatingGetDocument ||
            isValidatingGetDocumentFolders ||
            isValidatingGetDisplayedDocumentFolderDetail
          }
        />
      </CustomDialog>

      {newParentDocumentFolderDetail && (
        <ConfirmMoveDocumentDialog
          bot={bot}
          open={isOpenConfirmMoveDocumentDialog}
          targetDocument={targetDocument}
          currentParentDocumentFolderDetail={currentDocumentFolderDetail}
          newParentDocumentFolderDetail={newParentDocumentFolderDetail}
          isLoading={isValidatingGetNewParentDocumentFolderDetail}
          onCloseConfirmDialog={closeConfirmMoveDocumentDialog}
          onCloseTableDialog={onClose}
          refetch={refetch}
        />
      )}
    </>
  );
};
