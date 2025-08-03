import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import {
  Box,
  Divider,
  FormControlLabel,
  MenuItem,
  Paper,
  Radio,
  RadioGroup,
  Select,
  Skeleton,
  Stack,
  Switch,
  Tooltip,
  Typography,
} from "@mui/material";
import { useAsyncFn } from "react-use";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getPdfParserLabel, isChatGptBot } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { getComparator } from "@/libs/sort";
import {
  updateTenantBasicAi,
  updateTenantBasicAiMaxConversationTurns,
  useGetBots,
  useGetTenant,
  useUpdateTenantBasicAiPdfParser,
  useUpdateTenantBasicAiWebBrowsing,
} from "@/orval/backend-api";
import {
  Approach,
  Bot,
  ModelFamilyOrText2ImageModelFamily,
  PdfParser,
  UserTenant,
} from "@/orval/models/backend-api";

import { BasicAiList } from "../../BasicAiList";
import { CreateBasicAiDialog } from "../../CreateBasicAiDialog";

const comparator = getComparator<Bot>("asc", "model_family");

type Props = {
  tenant: UserTenant;
};

export const BasicAiSettings = ({ tenant }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { fetchUserInfo } = useUserInfo();

  const {
    open: openCreateBasicAiDialog,
    close: closeCreateBasicAiDialog,
    isOpen: isOpenCreateBasicAiDialog,
  } = useDisclosure({});

  const {
    isValidating: isLoadingGetTenant,
    error: getTenantError,
    data: tenantDetail,
    mutate: refetchTenant,
  } = useGetTenant(tenant.id);
  const {
    data: botsData,
    error: getBotsError,
    mutate: refetchBots,
  } = useGetBots({ status: ["active"] });

  if (getTenantError) {
    enqueueErrorSnackbar({ message: "テナントの取得に失敗しました。" });
  }
  if (getBotsError) {
    enqueueErrorSnackbar({ message: "基盤モデルの取得に失敗しました。" });
  }

  const bots = botsData?.bots ?? [];
  const basicAIs = bots.filter(bot => isChatGptBot(bot)).sort(comparator) ?? [];

  const allowedModelFamilies = tenant.allowed_model_families.model_families;

  const uncreatedModelFamilies = allowedModelFamilies.filter(
    modelFamily =>
      !basicAIs.some(
        bot =>
          (bot.approach === Approach.chat_gpt_default && bot.model_family === modelFamily) ||
          (bot.approach === Approach.text_2_image && bot.text2image_model_family === modelFamily),
      ),
  );

  const { isMutating: isLoadingEnableWebBrowsing, trigger: updateEnableWebBrowsing } =
    useUpdateTenantBasicAiWebBrowsing(tenant.id);
  const { isMutating: isLoadingPdfParser, trigger: updatePdfParser } =
    useUpdateTenantBasicAiPdfParser(tenant.id);

  const onChangeWebBrowsing = async (enableWebBrowsing: boolean) => {
    try {
      await updateEnableWebBrowsing({ enable_basic_ai_web_browsing: enableWebBrowsing });
      refetchTenant();
      fetchUserInfo();
      enqueueSuccessSnackbar({ message: "Web検索の設定を更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "Web検索の設定の更新に失敗しました。",
      });
    }
  };
  const onChangePdfParser = async (pdfParser: PdfParser) => {
    try {
      await updatePdfParser({ basic_ai_pdf_parser: pdfParser });
      refetchTenant();
      enqueueSuccessSnackbar({ message: "ドキュメント読み取りオプションの設定を更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "ドキュメント読み取りオプションの設定の更新に失敗しました。",
      });
    }
  };
  const [onUpdateBasicAiState, onUpdateBasicAi] = useAsyncFn(
    async (modelFamily: ModelFamilyOrText2ImageModelFamily, enabled: boolean) => {
      try {
        await updateTenantBasicAi(tenant.id, modelFamily, { enabled });
        refetchBots();
        enqueueSuccessSnackbar({ message: `基盤モデルを${enabled ? "作成" : "削除"}しました` });

        if (enabled) {
          closeCreateBasicAiDialog();
        }
      } catch (e) {
        const errMsg = getErrorMessage(e);
        enqueueErrorSnackbar({
          message: errMsg || `基盤モデルの${enabled ? "作成" : "削除"}に失敗しました。`,
        });
      }
    },
  );

  const [onUpdateBasicAiMaxConversationTurnsState, onUpdateBasicAiMaxConversationTurns] =
    useAsyncFn(async (maxConversationTurns: number) => {
      try {
        // nullをvalueとして選択できないため、0をnullに変換する
        const maxConversationTurnsForUpdate =
          maxConversationTurns === 0 ? null : maxConversationTurns;
        await updateTenantBasicAiMaxConversationTurns(tenant.id, {
          basic_ai_max_conversation_turns: maxConversationTurnsForUpdate,
        });
        refetchTenant();
        enqueueSuccessSnackbar({ message: "最大会話数の更新に成功しました。" });
      } catch (e) {
        const errMsg = getErrorMessage(e);
        enqueueErrorSnackbar({
          message: errMsg || "最大会話数の更新に失敗しました。",
        });
      }
    });

  const PdfParserRadio =
    isLoadingPdfParser || isLoadingGetTenant ? (
      <Skeleton variant="rectangular" width={25} height={25} />
    ) : (
      <Radio size="small" sx={{ p: 0.5 }} />
    );

  return (
    <>
      <Box>
        <ContentHeader>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Typography variant="h4">基盤モデル設定</Typography>
            <Tooltip
              title={
                uncreatedModelFamilies.length === 0 && (
                  <Typography variant="body2">全ての利用可能モデルが追加されています。</Typography>
                )
              }
              placement="top"
            >
              <Box>
                <PrimaryButton
                  text={
                    <Typography variant="button" sx={{ wordBreak: "keep-all" }}>
                      新規作成
                    </Typography>
                  }
                  startIcon={<AddOutlinedIcon />}
                  onClick={openCreateBasicAiDialog}
                  disabled={uncreatedModelFamilies.length === 0}
                />
              </Box>
            </Tooltip>
          </Stack>
        </ContentHeader>
        <Paper
          sx={{
            p: 2,
            borderRadius: "0 0 4px 4px",
          }}
          variant="outlined"
        >
          <Stack direction="row" gap={3}>
            <Stack gap={2} flex={1}>
              <Box>
                <Stack direction="row" alignItems="center" gap={2}>
                  <Typography variant="h5">Web検索</Typography>
                  {isLoadingEnableWebBrowsing || isLoadingGetTenant ? (
                    <Skeleton variant="rectangular" width={50} height={30} />
                  ) : (
                    <Switch
                      checked={tenantDetail?.enable_basic_ai_web_browsing}
                      onChange={e => {
                        onChangeWebBrowsing(e.target.checked);
                      }}
                      name="enable_basic_ai_web_browsing"
                    />
                  )}
                </Stack>
                <Typography variant="body2">
                  基盤モデルでWeb検索を可能にするかどうかを設定します。
                </Typography>
              </Box>
              {tenant.enable_document_intelligence && (
                <Box>
                  <Typography variant="h5">ドキュメント読み取りオプション</Typography>
                  <RadioGroup
                    name="pdf_parser"
                    value={tenantDetail?.basic_ai_pdf_parser}
                    onChange={e => {
                      const value = e.target.value as keyof typeof PdfParser;
                      onChangePdfParser(value);
                    }}
                    sx={{
                      px: 2,
                      py: 1,
                    }}
                  >
                    <Stack direction="row" alignItems="center">
                      <FormControlLabel
                        value="pypdf"
                        control={PdfParserRadio}
                        label={getPdfParserLabel(PdfParser.pypdf)}
                        sx={{ mr: 1 }}
                      />
                      <IconButtonWithTooltip
                        tooltipTitle="標準的な読み取りの方式です。資料の文字起こしのみを行います。"
                        color="primary"
                        icon={<HelpOutlineIcon sx={{ fontSize: 18 }} />}
                        iconButtonSx={{ p: 0 }}
                      />
                    </Stack>
                    <Stack direction="row" alignItems="center">
                      <FormControlLabel
                        value="document_intelligence"
                        control={PdfParserRadio}
                        label={getPdfParserLabel(PdfParser.document_intelligence)}
                        sx={{ mr: 1 }}
                      />
                      <IconButtonWithTooltip
                        tooltipTitle="資料のレイアウト構造を解析することでより人間が読む順序に近い文字起こしを行えます。複雑な表構造に対しても適切に解析が行われます。"
                        color="primary"
                        icon={<HelpOutlineIcon sx={{ fontSize: 18 }} />}
                        iconButtonSx={{ p: 0 }}
                      />
                    </Stack>
                  </RadioGroup>
                  <Typography variant="body2">
                    基盤モデルの添付ファイルの読み取り方法を設定します。より高度な読み取り方を選択することで、ファイルを添付した際の回答の精度向上が期待できます。
                  </Typography>
                </Box>
              )}
              <Stack>
                <Stack direction="row" alignItems="center" gap={2}>
                  <Typography variant="h5">最大会話数</Typography>
                  {isLoadingGetTenant || onUpdateBasicAiMaxConversationTurnsState.loading ? (
                    <Skeleton variant="rectangular" width={120} height={30} />
                  ) : (
                    <Select
                      size="small"
                      value={tenantDetail?.basic_ai_max_conversation_turns ?? 0}
                      onChange={e => onUpdateBasicAiMaxConversationTurns(Number(e.target.value))}
                      disabled={onUpdateBasicAiMaxConversationTurnsState.loading}
                      sx={{ minWidth: 80 }}
                    >
                      {Array.from({ length: 10 }, (_, i) => i + 1).map(value => (
                        <MenuItem key={value} value={value}>
                          {value}
                        </MenuItem>
                      ))}
                      <MenuItem value={0}>無制限</MenuItem>
                    </Select>
                  )}
                </Stack>
                <Spacer px={10} />
                <Typography variant="body2">基盤モデルの最大会話数を設定します。</Typography>
              </Stack>
            </Stack>
            <Divider variant="middle" orientation="vertical" flexItem />
            <Stack flex={1}>
              <Spacer px={8} />
              <BasicAiList
                basicAIs={basicAIs}
                onDelete={mf => onUpdateBasicAi(mf, false)}
                isLoading={onUpdateBasicAiState.loading}
              />
            </Stack>
          </Stack>
        </Paper>
      </Box>

      <CreateBasicAiDialog
        isOpen={isOpenCreateBasicAiDialog}
        close={closeCreateBasicAiDialog}
        allowedModelFamilies={allowedModelFamilies}
        uncreatedModelFamilies={uncreatedModelFamilies}
        onCreateBasicAi={mf => onUpdateBasicAi(mf, true)}
        isCreatingBasicAi={onUpdateBasicAiState.loading}
      />
    </>
  );
};
