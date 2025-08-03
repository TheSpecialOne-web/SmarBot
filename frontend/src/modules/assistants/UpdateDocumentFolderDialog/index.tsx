import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateDocumentFolder } from "@/orval/backend-api";
import { Bot, DocumentFolder, UpdateDocumentFolderParam } from "@/orval/models/backend-api";

import { UpdateDocumentFolderForm } from "./UpdateDocumentFolderForm";

type Props = {
  open: boolean;
  documentFolder: DocumentFolder;
  bot: Bot;
  onClose: () => void;
  refetch: () => void;
};

export const UpdateDocumentFolderDialog = ({
  open,
  documentFolder,
  bot,
  onClose,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger } = useUpdateDocumentFolder(bot.id, documentFolder.id);

  const updateDocumentFolder = async (param: UpdateDocumentFolderParam) => {
    try {
      await trigger(param);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "フォルダを更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "フォルダの更新に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} title="フォルダ編集">
      <UpdateDocumentFolderForm
        documentFolder={documentFolder}
        onSubmit={updateDocumentFolder}
        onClose={onClose}
      />
    </CustomDialog>
  );
};
