import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteDocument } from "@/orval/backend-api";
import { Bot, Document } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  document: Document;
  bot: Bot;
  onClose: () => void;
  refetch: () => void;
};

export const DeleteDocumentDialog = ({ open, document, bot, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useDeleteDocument(bot.id, document.id);

  const deleteDocument = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ドキュメントを削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ドキュメントの削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Typography>
      <Typography component="span" fontWeight="bold">
        {document.name}
      </Typography>
      を削除してもよろしいですか？
      <br />
      <Typography variant="caption">※反映には1分ほどかかります</Typography>
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="資料を削除"
      content={deleteDialogContents}
      buttonText="削除"
      onSubmit={deleteDocument}
      isLoading={isMutating}
    />
  );
};
