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
  DocumentFolder,
  DocumentFolderDetail,
  MoveDocumentFolderParam,
} from "@/orval/models/backend-api";

import { ConfirmMoveDocumentFolderDialog } from "../ConfirmMoveDocumentFolderDialog";
import { MoveDocumentFolderTable } from "./MoveDocumentFolderTable";

type Props = {
  bot: Bot;
  open: boolean;
  targetDocumentFolder: DocumentFolder;
  rootDocumentFolder: DocumentFolder;
  currentParentDocumentFolderDetail: DocumentFolderDetail;
  onClose: () => void;
  refetch: () => void;
};

export const MoveDocumentFolderDialog = ({
  bot,
  open,
  targetDocumentFolder,
  rootDocumentFolder,
  currentParentDocumentFolderDetail,
  onClose,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const [displayedDocumentFolderId, setDisplayedDocumentFolderId] = useState<string>(
    currentParentDocumentFolderDetail.id ?? rootDocumentFolder.id,
  );

  const [newParentDocumentFolderId, setNewParentDocumentFolderId] = useState<string | null>(null);

  const {
    isOpen: isOpenConfirmMoveDocumentFolderDialog,
    open: openConfirmMoveDocumentFolderDialog,
    close: closeConfirmMoveDocumentFolderDialog,
  } = useDisclosure({
    onClose: () => {
      setNewParentDocumentFolderId(null);
    },
  });

  const handleOpenConfirmMoveDocumentFolderDialog = (param: MoveDocumentFolderParam) => {
    setNewParentDocumentFolderId(param.new_parent_document_folder_id);
    openConfirmMoveDocumentFolderDialog();
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
  const displayedDocumentFolders = documentFoldersData?.document_folders ?? [];

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
            {targetDocumentFolder.name} を移動
          </Typography>
        }
        maxWidth="md"
        onClose={onClose}
      >
        <MoveDocumentFolderTable
          targetDocumentFolder={targetDocumentFolder}
          rootDocumentFolder={rootDocumentFolder}
          displayedDocumentFolderId={displayedDocumentFolderId}
          documents={documents}
          displayedDocumentFolders={displayedDocumentFolders}
          displayedDocumentFolderDetail={displayedDocumentFolderDetail}
          currentParentDocumentFolderDetail={currentParentDocumentFolderDetail}
          onMoveToFolder={handleMoveToFolder}
          onSubmit={handleOpenConfirmMoveDocumentFolderDialog}
          onClose={onClose}
          isLoading={
            isValidatingGetDocument ||
            isValidatingGetDocumentFolders ||
            isValidatingGetDisplayedDocumentFolderDetail
          }
        />
      </CustomDialog>

      {newParentDocumentFolderDetail && (
        <ConfirmMoveDocumentFolderDialog
          bot={bot}
          open={isOpenConfirmMoveDocumentFolderDialog}
          targetDocumentFolder={targetDocumentFolder}
          currentParentDocumentFolderDetail={currentParentDocumentFolderDetail}
          newParentDocumentFolderDetail={newParentDocumentFolderDetail}
          isLoading={isValidatingGetNewParentDocumentFolderDetail}
          onCloseConfirmDialog={closeConfirmMoveDocumentFolderDialog}
          onCloseTableDialog={onClose}
          refetch={refetch}
        />
      )}
    </>
  );
};
