import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useCreateTermV2 } from "@/orval/backend-api";
import { Bot, CreateTermParamV2 } from "@/orval/models/backend-api";

import { CreateOrUpdateTermForm } from "../CreateOrUpdateTermForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  botId: Bot["id"];
};

export const CreateTermDialog = ({ open, onClose, refetch, botId }: Props) => {
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();
  const { trigger: createTermTrigger } = useCreateTermV2(botId);

  const handleCreateTerm = async (param: CreateTermParamV2) => {
    try {
      await createTermTrigger(param);
      refetch();
      enqueueSuccessSnackbar({ message: "用語を追加しました。" });
      onClose();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "用語の追加に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} title="用語の追加" maxWidth="md">
      <CreateOrUpdateTermForm onClose={onClose} onSubmit={handleCreateTerm} />
    </CustomDialog>
  );
};
