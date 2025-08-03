import { TabContext, TabList, TabPanel } from "@mui/lab";
import { FormControlLabel, MenuItem, Stack, Switch, Tab, Tooltip, Typography } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { SyntheticEvent, useState } from "react";
import { Controller, useFieldArray, useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { APPROACH_VARIABLES } from "@/const/approach_variables";
import { modelNames } from "@/const/modelFamily";
import {
  getImageGenerationModelFamiliesFromAllowedModelFamilies,
  getTextGenerationModelFamiliesFromAllowedModelFamilies,
} from "@/libs/administrator/model";
import { displaySearchMethodForAdministrator } from "@/libs/searchMethod";
import {
  Approach,
  Bot,
  PdfParser,
  SearchMethod,
  Tenant,
  UpdateBotParam,
} from "@/orval/models/administrator-api";

type Props = {
  tenant: Tenant;
  bot: Bot;
  onClose: () => void;
  handleUpdateBot: (data: UpdateBotParam) => Promise<void>;
};

type TabItem = "basic-settings" | "approach-variables-settings";
const tabs = [
  {
    label: "基本情報",
    value: "basic-settings",
  },
  {
    label: "アプローチ変数",
    value: "approach-variables-settings",
  },
];

const handleWheel = (event: React.WheelEvent<HTMLInputElement>) => {
  event.currentTarget.blur();
};

export const UpdateBotForm = ({ tenant, bot, handleUpdateBot, onClose }: Props) => {
  const { blobContainerRenewal } = useFlags();
  const {
    control,
    handleSubmit,
    watch,
    formState: { isSubmitting },
  } = useForm<UpdateBotParam>({
    defaultValues: {
      name: bot.name,
      description: bot.description,
      index_name: bot.index_name,
      container_name: bot.container_name,
      approach: bot.approach,
      example_questions: bot.example_questions,
      approach_variables: [
        ...APPROACH_VARIABLES.map(variable => {
          const approachVariable = bot.approach_variables.find(item => item.name === variable.key);
          return {
            name: variable.key,
            value: approachVariable?.value || "",
          };
        }),
      ],
      search_method: bot?.search_method,
      response_generator_model_family: bot.response_generator_model_family,
      image_generator_model_family: bot?.image_generator_model_family,
      pdf_parser: bot?.pdf_parser || PdfParser.pypdf,
      enable_web_browsing: bot?.enable_web_browsing || false,
      enable_follow_up_questions: bot?.enable_follow_up_questions || false,
      icon_color: bot?.icon_color,
      max_conversation_turns: bot?.max_conversation_turns == null ? 0 : bot?.max_conversation_turns,
    },
  });

  const { fields } = useFieldArray({ control, name: "approach_variables" });

  const isBotWithData = ([Approach.neollm, Approach.ursa] as string[]).includes(watch("approach"));
  const isUrsaBot = watch("approach") === Approach.ursa;

  const [tabValue, setTabValue] = useState("basic-settings");

  const handleTabChange = (_event: SyntheticEvent, newValue: TabItem) => {
    setTabValue(newValue);
  };

  const onSubmit = async (data: UpdateBotParam) => {
    // data.approach_variablesのvalueが空だったら削除
    data.approach_variables = data.approach_variables.filter(variable => variable.value !== "");

    await handleUpdateBot(data);
  };
  const isImageGenerationBot = watch("approach") === Approach.text_2_image;
  const allowedTextGenerationModelFamilies = getTextGenerationModelFamiliesFromAllowedModelFamilies(
    tenant.allowed_model_families,
  );
  const allowedImageGenerationModelFamilies =
    getImageGenerationModelFamiliesFromAllowedModelFamilies(tenant.allowed_model_families);

  return (
    <TabContext value={tabValue}>
      <form noValidate onSubmit={handleSubmit(onSubmit)}>
        <CustomDialogContent>
          <TabList onChange={handleTabChange}>
            {tabs.map(tab => (
              <Tab key={tab.value} label={tab.label} value={tab.value} />
            ))}
          </TabList>
          <TabPanel
            value="basic-settings"
            sx={{
              px: 0,
            }}
          >
            <Stack gap={2}>
              <Stack>
                <CustomLabel label="テナント名" />
                <Typography variant="subtitle1">{tenant.name}</Typography>
              </Stack>
              <CustomTextField
                name="name"
                label="ボット名"
                fullWidth
                control={control}
                rules={{ required: "ボット名は必須です。" }}
              />
              <CustomTextField
                name="description"
                label="説明"
                fullWidth
                control={control}
                rules={{ required: "ボットの説明は必須です。" }}
                InputProps={{
                  multiline: true,
                }}
              />
              <CustomFormSelect
                name="approach"
                label="アプローチ"
                control={control}
                rules={{ required: "アプローチは必須です。" }}
              >
                {Object.entries(Approach).map(([key, value]) => (
                  <MenuItem key={key} value={value}>
                    {value}
                  </MenuItem>
                ))}
              </CustomFormSelect>
              {isUrsaBot && (
                <CustomTextField
                  name="index_name"
                  label="インデックス名 ( 編集不可 )"
                  fullWidth
                  control={control}
                  InputProps={{
                    readOnly: true,
                  }}
                />
              )}
              {!blobContainerRenewal && (
                <CustomTextField
                  name="container_name"
                  label="コンテナ名 ( 編集不可 )"
                  fullWidth
                  control={control}
                  InputProps={{
                    readOnly: true,
                  }}
                />
              )}
              {isBotWithData && (
                <CustomFormSelect name="search_method" label="検索方法" control={control}>
                  {Object.entries(SearchMethod).map(([key, value]) => (
                    <MenuItem key={key} value={value}>
                      {displaySearchMethodForAdministrator(value)}
                    </MenuItem>
                  ))}
                </CustomFormSelect>
              )}

              <CustomFormSelect
                name="pdf_parser"
                label="ドキュメント読み取りオプション"
                control={control}
                rules={{
                  required: "ドキュメント読み取りオプションは必須です。",
                }}
              >
                {tenant.available_pdf_parsers.map(parser => (
                  <MenuItem key={parser} value={parser}>
                    {parser}
                  </MenuItem>
                ))}
              </CustomFormSelect>
              <CustomFormSelect
                name="response_generator_model_family"
                label="回答生成モデル"
                control={control}
                rules={{ required: "回答生成モデルは必須です。" }}
              >
                {allowedTextGenerationModelFamilies.map(mf => (
                  <MenuItem key={mf} value={mf}>
                    {modelNames[mf]}
                  </MenuItem>
                ))}
              </CustomFormSelect>
              {isImageGenerationBot && (
                <CustomFormSelect
                  name="image_generator_model_family"
                  label="画像生成モデル"
                  control={control}
                  rules={{ required: "画像生成モデルは必須です。" }}
                >
                  {allowedImageGenerationModelFamilies.map(mf => (
                    <MenuItem key={mf} value={mf}>
                      {modelNames[mf]}
                    </MenuItem>
                  ))}
                </CustomFormSelect>
              )}
              <CustomTextField
                name="icon_color"
                label="アイコンの色"
                rules={{ required: "アイコンの色は必須です。" }}
                control={control}
                fullWidth
              />
              <CustomFormSelect
                name="max_conversation_turns"
                label="最大記憶対話数"
                control={control}
                rules={{ required: "最大記憶対話数は必須です。" }}
                tooltip="選択しているモデルの上限を超える場合、モデルの最大値が適用されます。"
              >
                {Array.from({ length: 20 }, (_, i) => i + 1).map(num => (
                  <MenuItem key={num} value={num}>
                    {num}
                  </MenuItem>
                ))}
                <MenuItem value={0}>無制限</MenuItem>
              </CustomFormSelect>
              <Controller
                name="enable_web_browsing"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={
                      <Switch
                        {...field}
                        checked={field.value}
                        onChange={e => {
                          field.onChange(e.target.checked);
                        }}
                        name="enable_web_browsing"
                      />
                    }
                    label="Web検索"
                    sx={{ ml: 0, width: "fit-content" }}
                  />
                )}
              />
              <Controller
                name="enable_follow_up_questions"
                control={control}
                render={({ field }) => (
                  <Tooltip
                    title={
                      !isBotWithData &&
                      "更問を生成できるのはドキュメントの参照が有効なときのみです。"
                    }
                    placement="top-start"
                    arrow
                  >
                    <FormControlLabel
                      disabled={!isBotWithData}
                      control={
                        <Switch
                          {...field}
                          checked={field.value}
                          onChange={e => {
                            field.onChange(e.target.checked);
                          }}
                          name="enable_follow_up_questions"
                        />
                      }
                      label="更問を生成する"
                      sx={{ ml: 0, width: "fit-content" }}
                    />
                  </Tooltip>
                )}
              />
            </Stack>
          </TabPanel>
          <TabPanel
            value={"approach-variables-settings"}
            sx={{
              px: 0,
            }}
          >
            <Stack gap={2}>
              {fields.map((field, index) => (
                <CustomTextField
                  key={field.id}
                  name={`approach_variables.${index}.value`}
                  label={APPROACH_VARIABLES[index].key}
                  fullWidth
                  control={control}
                  multiline={APPROACH_VARIABLES[index].type === "text"}
                  tooltip={APPROACH_VARIABLES[index].description}
                  disabled={APPROACH_VARIABLES[index].disabled}
                  type={APPROACH_VARIABLES[index].type}
                  rules={
                    APPROACH_VARIABLES[index].type === "number"
                      ? {
                          min: { value: 0, message: "0 以上の数値を入力してください。" },
                        }
                      : undefined
                  }
                  inputProps={{
                    onWheel: handleWheel,
                  }}
                />
              ))}
            </Stack>
          </TabPanel>
        </CustomDialogContent>
        <CustomDialogAction onClose={onClose} buttonText="保存" loading={isSubmitting} />
      </form>
    </TabContext>
  );
};
