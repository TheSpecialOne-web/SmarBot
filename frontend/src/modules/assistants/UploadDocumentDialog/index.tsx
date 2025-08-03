import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useCreateDocuments } from "@/orval/backend-api";
import {
  Bot,
  CreateDocumentsParam,
  CreateDocumentsParams,
  Document,
  DocumentFolder,
} from "@/orval/models/backend-api";

import { UploadDocumentForm } from "./UploadDocumentForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  bot: Bot;
  parentDocumentFolderId: DocumentFolder["id"] | null;
  documents: Document[];
};

export const UploadDocumentDialog = ({
  open,
  onClose,
  refetch,
  bot,
  parentDocumentFolderId,
  documents,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const params: CreateDocumentsParams = {
    parent_document_folder_id: parentDocumentFolderId || undefined,
  };

  const { trigger: uploadDocumentTrigger } = useCreateDocuments(bot.id, params);

  const handleUploadDocument = async (params: CreateDocumentsParam) => {
    if (params.files.length === 0) {
      enqueueErrorSnackbar({ message: "ファイルを選択してください。" });
      return;
    }
    try {
      await uploadDocumentTrigger(params);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ドキュメントのアップロードに成功しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ドキュメントのアップロードに失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="ドキュメント追加" maxWidth="md">
      <UploadDocumentForm onSubmit={handleUploadDocument} onClose={onClose} documents={documents} />
    </CustomDialog>
  );
};
