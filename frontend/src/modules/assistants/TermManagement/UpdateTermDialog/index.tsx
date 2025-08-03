import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateTermV2 } from "@/orval/backend-api";
import { Bot, TermV2, UpdateTermParamV2 } from "@/orval/models/backend-api";

import { CreateOrUpdateTermForm } from "../CreateOrUpdateTermForm";

type Props = {
  open: boolean;
  onClose: () => void;
  term: TermV2;
  refetch: () => void;
  assistantId: Bot["id"];
};

export const UpdateTermDialog = ({ open, onClose, refetch, term, assistantId }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: updateTerm } = useUpdateTermV2(assistantId, term.id);

  const handleUpdateTerm = async (param: UpdateTermParamV2) => {
    try {
      await updateTerm(param);
      enqueueSuccessSnackbar({ message: "用語を更新しました。" });
      refetch();
      onClose();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "用語の更新に失敗しました。",
      });
    }
  };

  return (
    <CustomDialog open={open} title="用語の編集" maxWidth="md">
      <CreateOrUpdateTermForm term={term} onClose={onClose} onSubmit={handleUpdateTerm} />
    </CustomDialog>
  );
};
