import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useCreateUser } from "@/orval/backend-api";
import { CreateUserParam } from "@/orval/models/backend-api";

import { CreateUserForm } from "./CreateUserForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const CreateUserDialog = ({ open, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: createUser } = useCreateUser();

  const onSubmit = async (params: CreateUserParam) => {
    try {
      await createUser(params);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ユーザーを作成しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ユーザーの作成に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="ユーザー作成">
      <CreateUserForm onSubmit={onSubmit} onClose={onClose} />
    </CustomDialog>
  );
};
