import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteDocumentFolder, useDeleteExternalDocumentFolder } from "@/orval/backend-api";
import { Bot, DocumentFolder } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  documentFolder: DocumentFolder;
  bot: Bot;
  onClose: () => void;
  refetch: () => void;
  isExternal?: boolean;
};

export const DeleteDocumentFolderDialog = ({
  open,
  documentFolder,
  bot,
  onClose,
  refetch,
  isExternal = false,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: deleteDocumentFolder, isMutating: isLoadingDeleteDocumentFolder } =
    useDeleteDocumentFolder(bot.id, documentFolder.id);
  const {
    trigger: deleteExternalDocumentFolder,
    isMutating: isLoadingDeleteExternalDocumentFolder,
  } = useDeleteExternalDocumentFolder(bot.id, documentFolder.id);

  const onDeleteDocumentFolder = async () => {
    try {
      await deleteDocumentFolder();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "フォルダを削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "フォルダの削除に失敗しました。" });
    }
  };
  const onDeleteExternalDocumentFolder = async () => {
    try {
      await deleteExternalDocumentFolder();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "フォルダの連携を解除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "フォルダの連携解除に失敗しました。" });
    }
  };

  const deleteDialogContents = isExternal ? (
    <Typography>
      連携を解除してもよろしいですか？
      <br />
      外部データ連携フォルダ
      <Typography component="span" fontWeight="bold" px={0.5}>
        {documentFolder.name}
      </Typography>
      は削除されます。
    </Typography>
  ) : (
    <Typography>
      <Typography component="span" fontWeight="bold">
        {documentFolder.name}
      </Typography>
      を削除してもよろしいですか？
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title={`フォルダの${isExternal ? "連携解除" : "削除"}`}
      content={deleteDialogContents}
      buttonText={isExternal ? "連携解除" : "削除"}
      onSubmit={isExternal ? onDeleteExternalDocumentFolder : onDeleteDocumentFolder}
      isLoading={isExternal ? isLoadingDeleteExternalDocumentFolder : isLoadingDeleteDocumentFolder}
    />
  );
};
