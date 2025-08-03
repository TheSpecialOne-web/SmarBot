import { HelpOutline } from "@mui/icons-material";
import {
  Card,
  Divider,
  FormControlLabel,
  Radio,
  RadioGroup,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { Controller, useFormContext } from "react-hook-form";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { CustomFormCheckbox } from "@/components/inputs/CustomFormCheckbox";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { Spacer } from "@/components/spacers/Spacer";
import { getPdfParserLabel } from "@/libs/bot";
import { AssistantIconSettings } from "@/modules/assistants/AssistantIconSettings";
import { ModelSelectForm } from "@/modules/assistants/ModelSelectForm";
import { BotTemplate, ModelFamily, UpdateBotTemplateParam } from "@/orval/models/administrator-api";
import { Approach, PdfParser } from "@/orval/models/backend-api";

type Props = {
  onSubmit: (
    data: UpdateBotTemplateParam,
    icon: File | null,
    currentIconUrl: string | null,
  ) => Promise<void>;
  assistantTemplate: BotTemplate;
};

export const UpdateAssistantTemplateForm = ({ onSubmit, assistantTemplate }: Props) => {
  const modelFamilies = Object.values(ModelFamily) as ModelFamily[];

  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
    watch,
    setValue,
  } = useFormContext<UpdateBotTemplateParam>();
  const [icon, setIcon] = useState<File | null>(null);
  const [iconUrl, setIconUrl] = useState<string | null>(assistantTemplate.icon_url || null);
  const [iconColor, setIconColor] = useState<string>(assistantTemplate.icon_color);

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

  const isCustomGpt = watch("approach") === Approach.custom_gpt;
  const isDataChat = watch("approach") === Approach.neollm;

  const handleWheel = (event: React.WheelEvent<HTMLInputElement>) => {
    event.currentTarget.blur();
  };

  return (
    <form onSubmit={handleSubmit(data => onSubmit(data, icon, iconUrl))}>
      <Card sx={{ p: 0 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" px={3} py={2}>
          <Typography variant="h4">アシスタントテンプレート編集</Typography>
          <PrimaryButton text="保存" type="submit" disabled={isSubmitting} loading={isSubmitting} />
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
          <ModelSelectForm<UpdateBotTemplateParam>
            control={control}
            modelFamilies={modelFamilies}
          />
          <CustomFormCheckbox name="enable_web_browsing" control={control} label="Web検索" />
          <CustomFormCheckbox
            name="approach"
            control={control}
            label="ドキュメントを参照する"
            checked={field => field.value === Approach.neollm}
            onChange={(e, field) => {
              if (!e.target.checked) {
                setValue("enable_follow_up_questions", false);
                setValue("pdf_parser", PdfParser.pypdf);
              }
              field.onChange(e.target.checked ? Approach.neollm : Approach.custom_gpt);
            }}
          />
          {isDataChat && (
            <>
              <CustomFormCheckbox
                name="enable_follow_up_questions"
                control={control}
                defaultValue={false}
                label="関連する質問の生成"
                disabled={isCustomGpt}
                tooltipTitle={"アシスタントの返答の内容に対する追加の質問を自動で生成します。"}
              />
              {!(watch("pdf_parser") === PdfParser.ai_vision) && (
                <Stack>
                  <Spacer px={8} />

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
                            sx={{ mr: 0 }}
                          />
                          <Spacer px={8} horizontal />
                          <IconButtonWithTooltip
                            tooltipTitle="標準的な読み取りの方式です。資料の文字起こしのみを行います。"
                            color="primary"
                            icon={<HelpOutline sx={{ fontSize: 18 }} />}
                            iconButtonSx={{ p: 0 }}
                          />
                        </Stack>
                        <Stack direction="row" alignItems="center">
                          <FormControlLabel
                            value="document_intelligence"
                            control={<Radio />}
                            label={getPdfParserLabel(PdfParser.document_intelligence)}
                            sx={{ mr: 0 }}
                          />
                          <Spacer px={8} horizontal />
                          <IconButtonWithTooltip
                            tooltipTitle="資料のレイアウト構造を解析することでより人間が読む順序に近い文字起こしを行えます。複雑な表構造に対しても適切に解析が行われます。"
                            color="primary"
                            icon={<HelpOutline sx={{ fontSize: 18 }} />}
                            iconButtonSx={{ p: 0 }}
                          />
                        </Stack>
                        <Stack direction="row" alignItems="center">
                          <FormControlLabel
                            value="llm_document_reader"
                            control={<Radio />}
                            label={getPdfParserLabel(PdfParser.llm_document_reader)}
                            sx={{ mr: 0 }}
                          />
                          <Spacer px={8} horizontal />
                          <IconButtonWithTooltip
                            tooltipTitle="上記機能に追加して、資料内のグラフやフロー図に対して文脈を考慮してAIが適切な説明を生成します。チャットへの添付ファイルには対応していません。"
                            color="primary"
                            icon={<HelpOutline sx={{ fontSize: 18 }} />}
                            iconButtonSx={{ p: 0 }}
                          />
                        </Stack>
                      </RadioGroup>
                    )}
                  />
                </Stack>
              )}
            </>
          )}
          <CustomTextField
            name="document_limit"
            label="取得するチャンク数"
            control={control}
            type="number"
            fullWidth
            rules={{
              required: "取得するチャンク数は必須です。",
              min: { value: 1, message: "1 以上の数値を入力してください。" },
            }}
            inputProps={{
              onWheel: handleWheel,
            }}
            tooltip="検索するチャンク数を設定します。精度が不十分だと感じた場合は、数を増やすことを検討してみてください。ただし増やしすぎると消費されるトークン数が増えるのに加え、回答に不要な情報まで検索してしまい回答精度が低下する可能性がありますので、用途に応じて適切な値を設定してください。"
          />
          <CustomTextField
            name="system_prompt"
            label="カスタム指示"
            control={control}
            fullWidth
            multiline
            minRows={8}
            maxRows={16}
            tooltip="プロンプトをカスタマイズします。アシスタントに遂行させる仕事内容を、プロンプトで設定してください。"
          />
        </Stack>
      </Card>
    </form>
  );
};
