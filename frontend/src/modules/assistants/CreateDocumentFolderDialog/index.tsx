import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useCreateDocumentFolder } from "@/orval/backend-api";
import { Bot, CreateDocumentFolderParam, DocumentFolder } from "@/orval/models/backend-api";

import { CreateDocumentFolderForm } from "./CreateDocumentFolderForm";

type Props = {
  open: boolean;
  bot: Bot;
  parentDocumentFolderId: DocumentFolder["id"] | null;
  onClose: () => void;
  refetch: () => void;
};

export const CreateDocumentFolderDialog = ({
  open,
  bot,
  parentDocumentFolderId,
  onClose,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger } = useCreateDocumentFolder(bot.id);

  const createFolder = async (param: CreateDocumentFolderParam) => {
    try {
      await trigger(param);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "フォルダを追加しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "フォルダの追加に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} title="フォルダ追加">
      <CreateDocumentFolderForm
        onSubmit={createFolder}
        onClose={onClose}
        parentDocumentFolderId={parentDocumentFolderId}
      />
    </CustomDialog>
  );
};
