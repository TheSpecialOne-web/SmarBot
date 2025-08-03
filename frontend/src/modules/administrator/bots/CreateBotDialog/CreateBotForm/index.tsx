import {
  Autocomplete,
  FormControlLabel,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { Controller, useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { DEFAULT_MAX_CONVERSATION_TURNS } from "@/const";
import { modelNames } from "@/const/modelFamily";
import {
  getImageGenerationModelFamiliesFromAllowedModelFamilies,
  getTextGenerationModelFamiliesFromAllowedModelFamilies,
} from "@/libs/administrator/model";
import { displaySearchMethodForAdministrator } from "@/libs/searchMethod";
import {
  Approach,
  CreateBotParam,
  Group,
  PdfParser,
  SearchMethod,
  Tenant,
} from "@/orval/models/administrator-api";
import { DEFAULT_ASSISTANT_ICON_COLOR } from "@/theme";

type Props = {
  onSubmit: ({ params, groupId }: { params: CreateBotParam; groupId: number }) => void;
  onClose: () => void;
  tenant: Tenant;
  groups: Group[];
};

export const CreateBotForm = ({ onSubmit, onClose, tenant, groups }: Props) => {
  const { blobContainerRenewal } = useFlags();

  const allowedTextGenerationModelFamilies = getTextGenerationModelFamiliesFromAllowedModelFamilies(
    tenant.allowed_model_families,
  );
  const allowedImageGenerationModelFamilies =
    getImageGenerationModelFamiliesFromAllowedModelFamilies(tenant.allowed_model_families);

  const {
    control,
    handleSubmit,
    watch,
    formState: { isSubmitting },
  } = useForm<CreateBotParam & { groupId: number }>({
    defaultValues: {
      name: "",
      description: "",
      example_questions: ["", "", ""],
      approach: Approach.neollm,
      search_method: SearchMethod.semantic_hybrid,
      response_generator_model_family: allowedTextGenerationModelFamilies[0],
      pdf_parser: PdfParser.pypdf,
      icon_color: DEFAULT_ASSISTANT_ICON_COLOR,
      enable_web_browsing: false,
      enable_follow_up_questions: false,
      approach_variables: [],
      max_conversation_turns: DEFAULT_MAX_CONVERSATION_TURNS,
    },
  });

  const isBotWithData = ([Approach.neollm, Approach.ursa] as string[]).includes(watch("approach"));
  const isUrsaBot = watch("approach") === Approach.ursa;
  const isImageGenerationBot = watch("approach") === Approach.text_2_image;

  return (
    <form
      noValidate
      onSubmit={handleSubmit(({ groupId, ...params }) => onSubmit({ params, groupId }))}
    >
      <CustomDialogContent>
        <Stack gap={2}>
          <Stack>
            <CustomLabel label="テナント名" />
            <Typography variant="subtitle1">{tenant.name}</Typography>
          </Stack>
          <Stack>
            <CustomLabel label="所属グループ" required />
            <Controller
              name="groupId"
              control={control}
              render={({ field: { onChange, value } }) => (
                <Autocomplete<Group["id"], false, true>
                  options={groups.map(({ id }) => id)}
                  getOptionLabel={option => groups.find(({ id }) => id === option)?.name ?? ""}
                  disableClearable
                  fullWidth
                  size="small"
                  renderInput={params => <TextField {...params} size="small" />}
                  value={value}
                  onChange={(_, data) => onChange(data)}
                />
              )}
            />
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
            control={control}
            rules={{ required: "ボットの説明は必須です。" }}
            fullWidth
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
              label="インデックス名"
              control={control}
              rules={{
                required: "インデックス名は必須です。",
                pattern: {
                  value: /^[a-z0-9]([a-z0-9]|-(?=[a-z0-9])){0,126}[a-z0-9]$/,
                  message:
                    "インデックス名は小文字のアルファベットと数字、ハイフンのみ使用できます。",
                },
              }}
              fullWidth
            />
          )}
          {!blobContainerRenewal && (
            <CustomTextField
              name="container_name"
              label="コンテナ名"
              control={control}
              rules={{
                required: "コンテナ名は必須です。",
                pattern: {
                  value: /^[a-z0-9]([a-z0-9]|-(?=[a-z0-9])){1,61}[a-z0-9]$/,
                  message: "コンテナ名は小文字のアルファベットと数字、ハイフンのみ使用できます。",
                },
              }}
              fullWidth
            />
          )}
          {isBotWithData && (
            <CustomFormSelect
              name="search_method"
              label="検索方法"
              control={control}
              rules={{ required: "検索方法は必須です。" }}
            >
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
          <Stack>
            <CustomFormSelect
              name="max_conversation_turns"
              label="最大記憶対話数"
              control={control}
              rules={{ required: "最大記憶対話数は必須です。" }}
            >
              {Array.from({ length: 20 }, (_, i) => i + 1).map(num => (
                <MenuItem key={num} value={num}>
                  {num}
                </MenuItem>
              ))}
              <MenuItem value={0}>無制限</MenuItem>
            </CustomFormSelect>
          </Stack>
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
                  !isBotWithData && "更問を生成できるのはドキュメントの参照が有効なときのみです。"
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
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="作成" loading={isSubmitting} />
    </form>
  );
};
