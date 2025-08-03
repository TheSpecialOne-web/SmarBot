import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteTenant } from "@/orval/administrator-api";
import { Tenant } from "@/orval/models/administrator-api";

type Props = {
  tenant: Tenant;
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const DeleteTenantDialog = ({ tenant, open, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useDeleteTenant(tenant.id);

  const handleConfirmDelete = async () => {
    try {
      await trigger();
      onClose();
      refetch();
      enqueueSuccessSnackbar({ message: "テナントを削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "テナントの削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Typography>
      <Typography component="span" fontWeight="bold">
        {tenant.name}
      </Typography>
      を削除してもよろしいですか？
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="テナント削除"
      content={deleteDialogContents}
      buttonText="削除"
      onSubmit={handleConfirmDelete}
      isLoading={isMutating}
    />
  );
};
