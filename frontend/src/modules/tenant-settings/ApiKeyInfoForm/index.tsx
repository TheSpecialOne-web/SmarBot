import { Stack, TextField, Tooltip, Typography } from "@mui/material";
import { grey } from "@mui/material/colors";
import { useState } from "react";

import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { ApiKey } from "@/orval/models/backend-api";
import { formatDate } from "@/utils/formatDate";

type Props = {
  apiKey: ApiKey;
};

export const ApiKeyInfoForm = ({ apiKey }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const [isCopiedApiKey, setIsCopiedApiKey] = useState<boolean>(false);
  const [isCopiedEndpoint, setIsCopiedEndpoint] = useState<boolean>(false);

  const endpoint = `${import.meta.env.VITE_EXTERNAL_API_URL}/endpoints/${apiKey.endpoint_id}`;
  const onCopyApiKeyClicked = async () => {
    try {
      const text = apiKey.api_key;
      if (!text) return;
      await navigator.clipboard.writeText(text);
      setIsCopiedApiKey(true);
    } catch (err) {
      enqueueErrorSnackbar({ message: "コピーに失敗しました。" });
    }
    setTimeout(() => setIsCopiedApiKey(false), 2000);
  };

  const onCopyEndpointClicked = async () => {
    try {
      await navigator.clipboard.writeText(endpoint);
      setIsCopiedEndpoint(true);
    } catch (err) {
      enqueueErrorSnackbar({ message: "コピーに失敗しました。" });
    }
    setTimeout(() => setIsCopiedEndpoint(false), 2000);
  };

  return (
    <CustomDialogContent>
      <Stack gap={2}>
        <Typography>
          APIキーを安全な場所に保存してください。
          <Typography component="span" fontWeight="bold">
            セキュリティの観点から、この画面は再表示されないため、必ずコピーしてください。
          </Typography>
          APIキーを紛失した場合、削除したのち新しいAPIキーを発行する必要があります。
        </Typography>
        <Stack direction="row">
          <Tooltip
            title={isCopiedEndpoint ? "コピーしました" : "クリックしてコピー"}
            placement="top"
          >
            <TextField
              type="text"
              defaultValue={endpoint}
              label="エンドポイント"
              variant="outlined"
              inputProps={{ readOnly: true }}
              fullWidth
              onClick={onCopyEndpointClicked}
              sx={{
                "&:hover": {
                  bgcolor: grey[200],
                  cursor: "pointer",
                  "& .MuiInputBase-input": {
                    cursor: "pointer",
                  },
                },
              }}
            />
          </Tooltip>
        </Stack>
        <Stack direction="row">
          <Tooltip title={isCopiedApiKey ? "コピーしました" : "クリックしてコピー"} placement="top">
            <TextField
              type="text"
              defaultValue={apiKey.api_key}
              label="APIキー"
              variant="outlined"
              inputProps={{ readOnly: true }}
              fullWidth
              onClick={onCopyApiKeyClicked}
              sx={{
                "&:hover": {
                  bgcolor: grey[200],
                  cursor: "pointer",
                  "& .MuiInputBase-input": {
                    cursor: "pointer",
                  },
                },
              }}
            />
          </Tooltip>
        </Stack>
        <Typography variant="body2" color={"grey.700"}>
          有効期限: {apiKey.expires_at ? formatDate(apiKey.expires_at) : "無期限"}
        </Typography>
      </Stack>
    </CustomDialogContent>
  );
};
