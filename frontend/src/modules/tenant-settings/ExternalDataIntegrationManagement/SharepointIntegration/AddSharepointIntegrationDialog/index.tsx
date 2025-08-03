import { Stack } from "@mui/material";
import { useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { SharepointConnectionKey, sharepointConnectionsInfo } from "@/const/externalDataConnection";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useCreateExternalDataConnection } from "@/orval/backend-api";
import { ExternalDataConnectionType } from "@/orval/models/backend-api";

type SharepointIntegrationInput = {
  [K in SharepointConnectionKey]: string;
};

type Props = {
  tenantId: number;
  isOpen: boolean;
  close: () => void;
  refetchExternalDataConnections: () => void;
};

export const AddSharepointIntegrationDialog = ({
  tenantId,
  isOpen,
  close,
  refetchExternalDataConnections,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const { control, handleSubmit } = useForm<SharepointIntegrationInput>();

  const { trigger: createExternalDataConnection, isMutating: loadingCreateExternalDataConnection } =
    useCreateExternalDataConnection(tenantId);
  const onSubmit = async (input: SharepointIntegrationInput) => {
    try {
      await createExternalDataConnection({
        external_data_connection_type: ExternalDataConnectionType.sharepoint,
        credentials: input,
      });
      enqueueSuccessSnackbar({ message: "SharePoint連携情報を登録しました" });
      close();
      refetchExternalDataConnections();
    } catch (error) {
      const errMsg = getErrorMessage(error);
      enqueueErrorSnackbar({ message: errMsg || "SharePoint連携情報の登録に失敗しました" });
    }
  };

  return (
    <CustomDialog title="SharePoint連携情報の入力" open={isOpen} onClose={close} maxWidth="md">
      <CustomDialogContent>
        <Stack direction="column" spacing={1}>
          {sharepointConnectionsInfo.map(({ key, label, description }) => (
            <CustomTextField
              key={key}
              control={control}
              name={key}
              label={label}
              tooltip={description}
              fullWidth
              required
              rules={{
                required: `${label}は必須です`,
              }}
            />
          ))}
        </Stack>
      </CustomDialogContent>
      <CustomDialogAction
        buttonText="送信"
        onClose={close}
        onSubmit={handleSubmit(onSubmit)}
        loading={loadingCreateExternalDataConnection}
      />
    </CustomDialog>
  );
};
