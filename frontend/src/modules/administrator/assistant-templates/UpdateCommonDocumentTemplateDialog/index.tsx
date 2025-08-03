import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateCommonDocumentTemplate } from "@/orval/administrator-api";
import {
  BotTemplate,
  CommonDocumentTemplate,
  UpdateCommonDocumentTemplateParam,
} from "@/orval/models/administrator-api";

import { UpdateCommonDocumentTemplateForm } from "./UpdateCommonDocumentTemplateForm";

type Props = {
  open: boolean;
  document: CommonDocumentTemplate;
  assistantTemplate: BotTemplate;
  onClose: () => void;
  refetch: () => void;
};

export const UpdateCommonDocumentTemplateDialog = ({
  open,
  document,
  assistantTemplate,
  onClose,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger } = useUpdateCommonDocumentTemplate(assistantTemplate.id, document.id);

  const updateCommonDocumentTemplate = async (param: UpdateCommonDocumentTemplateParam) => {
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
      <UpdateCommonDocumentTemplateForm
        document={document}
        onSubmit={updateCommonDocumentTemplate}
        onClose={onClose}
      />
    </CustomDialog>
  );
};
