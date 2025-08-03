import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import { Alert, IconButton, Paper, Stack, Typography } from "@mui/material";

import { CopyButton } from "@/components/buttons/CopyButton";
import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { Spacer } from "@/components/spacers/Spacer";
import { useCopy } from "@/hooks/useCopy";
import { ApiKey } from "@/orval/models/backend-api";
import { formatDate } from "@/utils/formatDate";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  apiKey: ApiKey;
};

export const ApiKeyDetailDialog = ({ isOpen, onClose, apiKey }: Props) => {
  const { isCopied, copy, reset } = useCopy();

  const handleClose = () => {
    onClose();
    // wait for the fade out animation of the dialog
    setTimeout(() => reset(), 500);
  };

  const queryParams = new URLSearchParams({
    endpoint_id: apiKey.endpoint_id,
    client_id: apiKey.id,
    bot_id: apiKey.bot.id.toString(),
    name: apiKey.bot.name,
    description: apiKey.bot.description,
    icon_color: apiKey.bot.icon_color,
    ...(apiKey.bot.icon_url && { icon_url: apiKey.bot.icon_url }),
  });
  const iframeCode = `<iframe
  src="${import.meta.env.VITE_APP_BASE_URL}/#/embed?${queryParams.toString()}"
  width="100%"
  height="100%">
</iframe>`;

  return (
    <CustomDialog
      open={isOpen}
      onClose={handleClose}
      title={<Typography variant="h5">{apiKey?.name}</Typography>}
      titleActions={
        <IconButton onClick={handleClose} sx={{ p: 0.5 }}>
          <CancelOutlinedIcon />
        </IconButton>
      }
      maxWidth="md"
    >
      <CustomDialogContent>
        <ContentHeader>
          <Typography variant="h4">概要</Typography>
        </ContentHeader>
        <Paper variant="outlined" sx={{ p: 2, borderRadius: "0 0 4px 4px" }}>
          <Typography variant="h5">アシスタント</Typography>
          <Typography p={1}>{apiKey.bot.name}</Typography>
          <Typography variant="h5">有効期限</Typography>
          <Typography p={1}>
            {apiKey.expires_at ? formatDate(apiKey.expires_at) : "無期限"}
          </Typography>
        </Paper>
        <Spacer px={16} />
        <ContentHeader>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h5">Webサイトへの埋め込み</Typography>
            <CopyButton isCopied={isCopied} copy={copy} text={iframeCode} />
          </Stack>
          <Spacer px={8} />
          <Alert severity="warning" sx={{ p: 0.5 }}>
            Webサイトに埋め込む場合、第三者が {apiKey.bot.name}{" "}
            に紐づくドキュメントを閲覧できるようになることに注意してください。
          </Alert>
        </ContentHeader>
        <Paper variant="outlined" sx={{ borderRadius: "0 0 4px 4px" }}>
          <code>
            <Typography
              fontSize={12}
              fontFamily="monospace"
              sx={{
                whiteSpace: "pre",
                p: 2,
                borderRadius: 4,
                overflowX: "auto",
              }}
            >
              {iframeCode}
            </Typography>
          </code>
        </Paper>
      </CustomDialogContent>
    </CustomDialog>
  );
};
