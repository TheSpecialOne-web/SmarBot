import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useUserInfo } from "@/hooks/useUserInfo";
import { useDeleteTenantGuideline } from "@/orval/backend-api";
import { Guideline } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  guideline: Guideline;
};

export const DeleteTenantGuidelineDialog = ({ open, onClose, refetch, guideline }: Props) => {
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();
  const {
    userInfo: { tenant },
  } = useUserInfo();

  const { trigger, isMutating } = useDeleteTenantGuideline(tenant.id, guideline.id);

  const deleteTenantGuideline = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ガイドラインを削除しました。" });
    } catch (e) {
      enqueueErrorSnackbar({ message: "ガイドラインの削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Typography>
      <Typography component="span" fontWeight="bold">
        {guideline.filename}
      </Typography>
      を削除してもよろしいですか？
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="ガイドライン削除"
      content={deleteDialogContents}
      buttonText="削除"
      onSubmit={deleteTenantGuideline}
      isLoading={isMutating}
    />
  );
};
