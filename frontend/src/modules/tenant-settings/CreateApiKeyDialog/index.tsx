import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import { IconButton } from "@mui/material";
import { useState } from "react";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useCreateApiKey } from "@/orval/backend-api";
import { ApiKey, CreateApiKeyParam } from "@/orval/models/backend-api";

import { ApiKeyInfoForm } from "../ApiKeyInfoForm";
import { CreateApiKeyForm } from "../CreateApiKeyForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const CreateApiKeyDialog = ({ open, onClose, refetch }: Props) => {
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();
  const { trigger: createApiKey } = useCreateApiKey();

  const [createdApiKey, setCreatedApiKey] = useState<ApiKey | undefined>();
  const isCreated = Boolean(createdApiKey);

  const resetCreatedApiKeyInfo = () => {
    setCreatedApiKey(undefined);
  };

  const onSubmit = async (params: CreateApiKeyParam) => {
    try {
      const createdApiKey = await createApiKey(params);
      setCreatedApiKey(createdApiKey);
      refetch();
      enqueueSuccessSnackbar({ message: "APIキーを作成しました" });
    } catch (error) {
      enqueueErrorSnackbar({ message: "APIキーの作成に失敗しました" });
    }
  };

  return (
    <CustomDialog
      open={open}
      onClose={onClose}
      title={isCreated ? "APIキーを保存" : "APIキーを作成"}
      maxWidth="md"
      disableBackdropClick={isCreated}
      titleActions={
        isCreated && (
          <IconButton
            onClick={() => {
              resetCreatedApiKeyInfo();
              onClose();
            }}
            sx={{ p: 0.5 }}
          >
            <CancelOutlinedIcon />
          </IconButton>
        )
      }
    >
      {isCreated && createdApiKey ? (
        <ApiKeyInfoForm apiKey={createdApiKey} />
      ) : (
        <CreateApiKeyForm onSubmit={onSubmit} onClose={onClose} />
      )}
    </CustomDialog>
  );
};
