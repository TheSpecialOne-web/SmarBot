import { Box, Divider, Paper, Skeleton, Stack, Switch, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { modelNames } from "@/const/modelFamily";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getPdfParserLabel } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { useGetBotTemplate, useUpdateBotTemplate } from "@/orval/administrator-api";
import { BotTemplate } from "@/orval/models/administrator-api";
import { Approach } from "@/orval/models/backend-api";

type Props = {
  assistantTemplate: BotTemplate;
  isLoadingSelectAssistantTemplate: boolean;
  refetch: () => void;
};

export const AssistantTemplateOverview = ({
  assistantTemplate,
  isLoadingSelectAssistantTemplate,
  refetch,
}: Props) => {
  const navigate = useNavigate();
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();

  const { mutate: refetchBotTemplate } = useGetBotTemplate(assistantTemplate.id);

  const {
    isOpen: isChangeStatusDialogOpen,
    open: openChangeStatusDialog,
    close: closeChangeStatusDialog,
  } = useDisclosure({});

  const { isMutating: loadingChageStatus, trigger: updateBotTemplate } = useUpdateBotTemplate(
    assistantTemplate.id,
  );

  const handleChageStatus = async () => {
    try {
      await updateBotTemplate({
        ...assistantTemplate,
        is_public: !assistantTemplate.is_public,
      });
      enqueueSuccessSnackbar({
        message: "アシスタントテンプレートの公開状況を更新しました。",
      });
      closeChangeStatusDialog();
      refetchBotTemplate();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "アシスタントテンプレートの更新に失敗しました。",
      });
    }
  };

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">概要</Typography>
          <Stack direction="row" gap={2}>
            <Stack direction="row" alignItems="center">
              <Typography variant="body1">公開</Typography>
              <Switch checked={assistantTemplate.is_public} onChange={openChangeStatusDialog} />
            </Stack>
            <RefreshButton onClick={refetch} />
            <PrimaryButton
              text={<Typography variant="button">編集</Typography>}
              onClick={() => navigate("edit")}
            />
          </Stack>
        </Stack>
      </ContentHeader>
      <Paper
        sx={{
          padding: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <Box sx={{ display: "flex", flexGrow: 1 }}>
          <Stack flex={1} spacing={2}>
            <Box>
              <Typography variant="h5" gutterBottom>
                アイコン
              </Typography>
              <Box sx={{ px: 0.75 }}>
                <AssistantAvatar
                  size={45}
                  iconUrl={assistantTemplate.icon_url}
                  iconColor={assistantTemplate.icon_color}
                />
              </Box>
            </Box>

            <Box>
              <Typography variant="h5" gutterBottom>
                名前
              </Typography>
              {isLoadingSelectAssistantTemplate ? (
                <Skeleton animation="pulse" variant="text" width="80%" height={30} />
              ) : (
                <Typography pl={1}>{assistantTemplate.name}</Typography>
              )}
            </Box>
            <Box>
              <Typography variant="h5" gutterBottom>
                説明
              </Typography>
              {isLoadingSelectAssistantTemplate ? (
                <Skeleton animation="pulse" variant="text" width="80%" height={30} />
              ) : (
                <Typography
                  px={1}
                  sx={{
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {assistantTemplate.description}
                </Typography>
              )}
            </Box>
            <Box>
              <Typography variant="h5" gutterBottom>
                モデル
              </Typography>
              {isLoadingSelectAssistantTemplate ? (
                <Skeleton animation="pulse" variant="text" width="80%" height={30} />
              ) : (
                <Typography pl={1}>{modelNames[assistantTemplate.model_family]}</Typography>
              )}
            </Box>
            <Box>
              <Typography variant="h5" gutterBottom>
                ドキュメントの参照
              </Typography>
              {isLoadingSelectAssistantTemplate ? (
                <Skeleton animation="pulse" variant="text" width="80%" height={30} />
              ) : (
                <Typography pl={1}>
                  {assistantTemplate.approach == Approach.neollm ? "有効" : "無効"}
                </Typography>
              )}
            </Box>
            {assistantTemplate.approach === Approach.neollm && (
              <Box>
                <Typography variant="h5" gutterBottom>
                  関連する質問の生成
                </Typography>
                {isLoadingSelectAssistantTemplate ? (
                  <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                ) : (
                  <Typography pl={1}>
                    {assistantTemplate.enable_follow_up_questions ? "有効" : "無効"}
                  </Typography>
                )}
              </Box>
            )}
            {assistantTemplate.approach === Approach.neollm && (
              <Box>
                <Typography variant="h5" gutterBottom>
                  資料読み取りオプション
                </Typography>
                {isLoadingSelectAssistantTemplate ? (
                  <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                ) : (
                  <Typography pl={1}>{getPdfParserLabel(assistantTemplate.pdf_parser)}</Typography>
                )}
              </Box>
            )}
            <Box>
              <Typography variant="h5">Web検索機能</Typography>
              {isLoadingSelectAssistantTemplate ? (
                <Skeleton animation="pulse" variant="text" width="80%" height={30} />
              ) : (
                <Typography pl={1}>
                  {assistantTemplate.enable_web_browsing == true ? "有効" : "無効"}
                </Typography>
              )}
            </Box>
          </Stack>

          <Divider orientation="vertical" flexItem />

          <Stack flex={1} spacing={2} pl={2}>
            <Box sx={{ whiteSpace: "pre-wrap" }}>
              <Typography variant="h5">カスタム指示</Typography>
              {isLoadingSelectAssistantTemplate ? (
                <Skeleton animation="pulse" variant="text" width="80%" height={30} />
              ) : (
                <Typography pl={1}>{assistantTemplate.system_prompt || "未設定"}</Typography>
              )}
            </Box>
          </Stack>
        </Box>
      </Paper>

      <ConfirmDialog
        open={isChangeStatusDialogOpen}
        onClose={closeChangeStatusDialog}
        title="公開状況の変更"
        content={`'${assistantTemplate.name}'を${
          assistantTemplate.is_public ? "非公開に" : "公開"
        }してもよろしいですか？`}
        buttonText={assistantTemplate.is_public ? "非公開" : "公開"}
        color={assistantTemplate.is_public ? "error" : "info"}
        onSubmit={handleChageStatus}
        isLoading={loadingChageStatus}
      />
    </>
  );
};
