import { HelpOutline } from "@mui/icons-material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Autocomplete,
  Card,
  Divider,
  FormControlLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  StyledAccordion,
  StyledAccordionDetails,
  StyledAccordionSummary,
} from "@/components/accordions/styledAccordions";
import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { CustomFormCheckbox } from "@/components/inputs/CustomFormCheckbox";
import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { Spacer } from "@/components/spacers/Spacer";
import { DEFAULT_MAX_CONVERSATION_TURNS } from "@/const";
import { getPdfParserLabel } from "@/libs/bot";
import { getTextGenerationModelFamiliesFromAllowedModelFamilies } from "@/libs/model";
import { displaySearchMethodForUser, SEARCH_METHODS_FOR_USER } from "@/libs/searchMethod";
import { AssistantIconSettings } from "@/modules/assistants/AssistantIconSettings";
import { ModelSelectForm } from "@/modules/assistants/ModelSelectForm";
import {
  Approach,
  CreateBotParam,
  Group,
  ModelFamiliesAndText2ImageModelFamilies,
  ModelFamily,
  PdfParser,
  SearchMethod,
} from "@/orval/models/backend-api";
import { DEFAULT_ASSISTANT_ICON_COLOR } from "@/theme";

export const DEFAULT_SYSTEM_PROMPT_FOR_CUSTOM_GPT = `あなたはプロの営業マンです。\n以下の{要件}を満たすため、{ユーザーからの入力}を元に回答を生成してください。\n\n# 要件\n入力された企業に関して、営業をかける際に役立つ情報をまとめてください\n\n# ユーザーからの入力\n企業名`;
export const DEFAULT_SYSTEM_PROMPT_FOR_NEOLLM = `あなたは優秀なビジネスマンです。\n以下の{要件}を満たすため、{制約条件}に気をつけながら、{ユーザーからの入力}と{学習済みドキュメント}を元に回答を生成してください。\n\n# 要件:\n社員からの社内マニュアルに関する質問に対して回答してください\n\n# 制約条件:\n新入社員にもわかるようなわかりやすい表現で答えてください\n\n# ユーザーからの入力\n社内マニュアルに関する質問\n\n# 学習済みドキュメント\n社内マニュアル`;
export const DEFAULT_DOCUMENT_LIMIT = 5;

type Props = {
  onSubmit: ({
    createBotParam,
    groupId,
    icon,
  }: {
    createBotParam: CreateBotParam;
    groupId: number;
    icon: File | null;
  }) => Promise<void>;
  groups: Group[];
  defaultGroup?: Group;
  defaultModelFamily: ModelFamily;
  allowedModelFamilies: ModelFamiliesAndText2ImageModelFamilies;
  enableDocumentIntelligence: boolean;
  enableLLMDocumentReader: boolean;
  iconUrl: string | null;
  setIconUrl: (url: string | null) => void;
};

export const CreateAssistantForm = ({
  onSubmit,
  groups,
  defaultGroup,
  defaultModelFamily,
  allowedModelFamilies,
  enableDocumentIntelligence,
  enableLLMDocumentReader,
  iconUrl,
  setIconUrl,
}: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
    watch,
    setValue,
  } = useForm<CreateBotParam & { groupId: number }>({
    defaultValues: {
      name: "",
      description: "",
      example_questions: ["", "", ""],
      approach: Approach.custom_gpt,
      model_family: defaultModelFamily,
      system_prompt: DEFAULT_SYSTEM_PROMPT_FOR_CUSTOM_GPT,
      document_limit: DEFAULT_DOCUMENT_LIMIT,
      pdf_parser: PdfParser.pypdf,
      enable_web_browsing: false,
      enable_follow_up_questions: false,
      icon_color: DEFAULT_ASSISTANT_ICON_COLOR,
      search_method: SearchMethod.semantic_hybrid,
      max_conversation_turns: DEFAULT_MAX_CONVERSATION_TURNS,
      groupId: defaultGroup?.id,
    },
  });
  const [icon, setIcon] = useState<File | null>(null);
  const [iconColor, setIconColor] = useState<string>(DEFAULT_ASSISTANT_ICON_COLOR);

  const deleteIcon = () => {
    setIcon(null);
    setIconUrl(null);
  };

  const setFormIcon = (icon: File) => {
    setIcon(icon);
    setIconUrl(URL.createObjectURL(icon));
  };

  const setFormIconColor = (color: string) => {
    setIconColor(color);
    setValue("icon_color", color);
  };

  const allowedTextGenerationModelFamilies =
    getTextGenerationModelFamiliesFromAllowedModelFamilies(allowedModelFamilies);

  const isCustomGpt = watch("approach") === Approach.custom_gpt;
  const isDataChat = watch("approach") === Approach.neollm;

  return (
    <form
      onSubmit={handleSubmit(({ groupId, ...createBotParam }) =>
        onSubmit({ createBotParam, groupId, icon }),
      )}
    >
      <Card sx={{ p: 0 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" px={3} py={2}>
          <Typography variant="h4">アシスタント作成</Typography>
          <PrimaryButton text="作成" type="submit" disabled={isSubmitting} loading={isSubmitting} />
        </Stack>
        <Divider />
        <Stack gap={2} p={3}>
          <AssistantIconSettings
            setFormIcon={setFormIcon}
            iconColor={iconColor}
            setFormIconColor={setFormIconColor}
            iconUrl={iconUrl}
            deleteIcon={deleteIcon}
          />
          <Stack>
            <CustomLabel label="所属グループ" required />
            <Controller
              name="groupId"
              control={control}
              render={({ field: { onChange, value } }) => (
                <Autocomplete<Group["id"], false, true>
                  options={defaultGroup ? [defaultGroup.id] : groups.map(({ id }) => id)}
                  getOptionLabel={option =>
                    defaultGroup
                      ? defaultGroup.name
                      : groups.find(({ id }) => id === option)?.name ?? ""
                  }
                  disableClearable
                  fullWidth
                  size="small"
                  renderInput={params => <TextField {...params} size="small" />}
                  value={value}
                  onChange={(_, data) => onChange(data)}
                  disabled={Boolean(defaultGroup)}
                />
              )}
            />
          </Stack>
          <CustomTextField
            name="name"
            label="名前"
            fullWidth
            control={control}
            rules={{ required: "名前は必須です。" }}
            tooltip="アシスタントの名前です。分かりやすい名前を付けてください（回答の精度には影響しません）。"
          />
          <CustomTextField
            name="description"
            label="説明"
            control={control}
            rules={{ required: "説明は必須です。" }}
            fullWidth
            InputProps={{
              multiline: true,
            }}
            tooltip="アシスタントに関する説明文です。このアシスタントの仕事内容がわかる文章を付けてください（回答の精度には影響しません）。"
          />

          <ModelSelectForm<CreateBotParam & { groupId: number }>
            control={control}
            modelFamilies={allowedTextGenerationModelFamilies}
          />

          <CustomFormCheckbox name="enable_web_browsing" control={control} label="Web検索" />

          <CustomFormCheckbox
            label="ドキュメントを参照する"
            name="approach"
            control={control}
            checked={field => field.value === Approach.neollm}
            onChange={(e, field) => {
              field.onChange(e.target.checked ? Approach.neollm : Approach.custom_gpt);
              if (e.target.checked) {
                setValue("system_prompt", DEFAULT_SYSTEM_PROMPT_FOR_NEOLLM);
                setValue("search_method", SearchMethod.semantic_hybrid);
              } else {
                setValue("enable_follow_up_questions", false);
                setValue("pdf_parser", PdfParser.pypdf);
                setValue("system_prompt", DEFAULT_SYSTEM_PROMPT_FOR_CUSTOM_GPT);
                setValue("search_method", undefined);
              }
            }}
          />
          {isDataChat && (
            <>
              <CustomFormCheckbox
                name="enable_follow_up_questions"
                defaultValue={false}
                control={control}
                label="関連する質問の生成"
                disabled={isCustomGpt}
                tooltipTitle={"アシスタントの返答の内容に対する追加の質問を自動で生成します。"}
              />
              {!(watch("pdf_parser") === PdfParser.ai_vision) && enableDocumentIntelligence && (
                <Stack>
                  <Spacer px={4} />

                  <CustomLabel
                    label="ドキュメント読み取りオプション"
                    tooltip="ドキュメントをアシスタントに追加する際に行われる読み取りの方式を選択できます。より高度な読み取り方を選択することで、ドキュメントを参照した回答の精度向上が期待できます。"
                  />

                  <Controller
                    name="pdf_parser"
                    defaultValue="pypdf"
                    control={control}
                    render={({ field }) => (
                      <RadioGroup
                        {...field}
                        name="pdf_parser"
                        value={watch("pdf_parser")}
                        onChange={e => {
                          const value = e.target.value as keyof typeof PdfParser;
                          setValue("pdf_parser", PdfParser[value]);
                        }}
                      >
                        <Stack direction="row" alignItems="center">
                          <FormControlLabel
                            value="pypdf"
                            control={<Radio />}
                            label={getPdfParserLabel(PdfParser.pypdf)}
                            sx={{ mr: 1 }}
                          />
                          <IconButtonWithTooltip
                            tooltipTitle="標準的な読み取りの方式です。資料の文字起こしのみを行います。"
                            color="primary"
                            icon={<HelpOutline sx={{ fontSize: 18 }} />}
                            iconButtonSx={{ p: 0 }}
                          />
                        </Stack>
                        {enableDocumentIntelligence && (
                          <Stack direction="row" alignItems="center">
                            <FormControlLabel
                              value="document_intelligence"
                              control={<Radio />}
                              label={getPdfParserLabel(PdfParser.document_intelligence)}
                              sx={{ mr: 1 }}
                            />
                            <IconButtonWithTooltip
                              tooltipTitle="資料のレイアウト構造を解析することでより人間が読む順序に近い文字起こしを行えます。複雑な表構造に対しても適切に解析が行われます。"
                              color="primary"
                              icon={<HelpOutline sx={{ fontSize: 18 }} />}
                              iconButtonSx={{ p: 0 }}
                            />
                          </Stack>
                        )}
                        {enableLLMDocumentReader && (
                          <Stack direction="row" alignItems="center">
                            <FormControlLabel
                              value="llm_document_reader"
                              control={<Radio />}
                              label={getPdfParserLabel(PdfParser.llm_document_reader)}
                              sx={{ mr: 1 }}
                            />
                            <IconButtonWithTooltip
                              tooltipTitle="上記機能に追加して、資料内のグラフやフロー図に対して文脈を考慮してAIが適切な説明を生成します。チャットへの添付ファイルには対応していません。"
                              color="primary"
                              icon={<HelpOutline sx={{ fontSize: 18 }} />}
                              iconButtonSx={{ p: 0 }}
                            />
                          </Stack>
                        )}
                      </RadioGroup>
                    )}
                  />
                </Stack>
              )}
            </>
          )}
          <CustomTextField
            name="system_prompt"
            label="カスタム指示"
            control={control}
            fullWidth
            multiline
            minRows={8}
            maxRows={16}
            tooltip="プロンプトをカスタマイズします。プロンプト例がデフォルトで入っています。アシスタントに遂行させる仕事内容を、プロンプトで設定してください。"
          />
          <StyledAccordion>
            <StyledAccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ fontWeight: 600 }}>
              詳細設定
            </StyledAccordionSummary>
            <StyledAccordionDetails>
              <Stack gap={2}>
                {isDataChat && (
                  <>
                    <CustomTextField
                      name="document_limit"
                      label="取得するチャンク数"
                      control={control}
                      type="number"
                      fullWidth
                      rules={{
                        required: "取得するチャンク数は必須です。",
                        min: { value: 1, message: "1 以上 20 以下の数値を入力してください。" },
                        max: { value: 20, message: "1 以上 20 以下の数値を入力してください。" },
                      }}
                      tooltip="検索するチャンク数を設定します。精度が不十分だと感じた場合は、数を増やすことを検討してみてください。ただし増やしすぎると消費されるトークン数が増えるのに加え、回答に不要な情報まで検索してしまい回答精度が低下する可能性がありますので、用途に応じて適切な値を設定してください。"
                    />
                    <CustomFormSelect
                      name="search_method"
                      label="検索方法"
                      control={control}
                      rules={{ required: "検索方法は必須です。" }}
                      tooltip={
                        <Typography fontSize={14}>
                          内容や文脈を考慮して探したい場合は「高精度検索」を選択してください。
                          <br />
                          特定の単語や文字列を探したい場合「キーワード検索」を選択してください。
                        </Typography>
                      }
                    >
                      {SEARCH_METHODS_FOR_USER.map(value => (
                        <MenuItem key={value} value={value}>
                          {displaySearchMethodForUser(value)}
                        </MenuItem>
                      ))}
                    </CustomFormSelect>
                  </>
                )}
                <CustomFormSelect
                  name="max_conversation_turns"
                  label="最大記憶対話数"
                  control={control}
                  rules={{ required: "最大記憶対話数は必須です。" }}
                  tooltip="選択しているモデルの上限を超える場合、モデルの最大値が適用されます。"
                >
                  {Array.from({ length: 10 }, (_, i) => i + 1).map(num => (
                    <MenuItem key={num} value={num}>
                      {num}
                    </MenuItem>
                  ))}
                  <MenuItem value={0}>無制限</MenuItem>
                </CustomFormSelect>
              </Stack>
            </StyledAccordionDetails>
          </StyledAccordion>
        </Stack>
      </Card>
    </form>
  );
};
