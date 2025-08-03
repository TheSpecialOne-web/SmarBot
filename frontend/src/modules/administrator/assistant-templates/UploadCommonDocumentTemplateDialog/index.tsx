import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useCreateCommonDocumentTemplate } from "@/orval/administrator-api";
import {
  BotTemplate,
  CommonDocumentTemplate,
  CreateCommonDocumentTemplateParam,
} from "@/orval/models/administrator-api";

import { UploadCommonDocumentTemplateForm } from "./UploadCommonDocumentTemplateForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  assistantTemplate: BotTemplate;
  documents: CommonDocumentTemplate[];
};

export const UploadCommonDocumentTemplateDialog = ({
  open,
  onClose,
  refetch,
  assistantTemplate,
  documents,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const { trigger: uploadDocumentTrigger } = useCreateCommonDocumentTemplate(assistantTemplate.id);

  const handleUploadCommonDocumentTemplate = async (params: CreateCommonDocumentTemplateParam) => {
    if (params.files.length === 0) {
      enqueueErrorSnackbar({ message: "ファイルを選択してください。" });
      return;
    }
    try {
      await uploadDocumentTrigger(params);
      enqueueSuccessSnackbar({ message: "ドキュメントのアップロードに成功しました。" });
      refetch();
      onClose();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ドキュメントのアップロードに失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="ドキュメント追加" maxWidth="md">
      <UploadCommonDocumentTemplateForm
        onSubmit={handleUploadCommonDocumentTemplate}
        onClose={onClose}
        documents={documents}
      />
    </CustomDialog>
  );
};
