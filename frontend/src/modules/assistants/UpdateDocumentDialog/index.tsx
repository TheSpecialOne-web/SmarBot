import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { isUrsaBot } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { useUpdateDocument } from "@/orval/backend-api";
import { Bot, Document, UpdateDocumentParam } from "@/orval/models/backend-api";

import { UpdateDocumentForm } from "./UpdateDocumentForm";

type Props = {
  open: boolean;
  document: Document;
  bot: Bot;
  onClose: () => void;
  refetch: () => void;
};

export const UpdateDocumentDialog = ({ open, document, bot, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger } = useUpdateDocument(bot.id, document.id);

  const updateDocument = async (param: UpdateDocumentParam) => {
    try {
      await trigger(param);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ドキュメントを更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ドキュメントの更新に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} title="ドキュメント編集">
      <UpdateDocumentForm
        document={document}
        onSubmit={updateDocument}
        onClose={onClose}
        isUrsaBot={isUrsaBot(bot)}
      />
    </CustomDialog>
  );
};
