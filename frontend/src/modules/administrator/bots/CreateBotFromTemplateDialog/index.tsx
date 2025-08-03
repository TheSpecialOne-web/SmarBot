import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import {
  Autocomplete,
  Box,
  Button,
  DialogActions,
  IconButton,
  Stack,
  TextField,
} from "@mui/material";
import { useState } from "react";
import { useAsyncFn } from "react-use";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { CircularLoading } from "@/components/loadings/CircularLoading";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getTextGenerationModelFamiliesFromAllowedModelFamilies } from "@/libs/administrator/model";
import { getErrorMessage } from "@/libs/error";
import { createBot, useGetBotTemplates } from "@/orval/administrator-api";
import {
  Approach,
  BotTemplate,
  CreateBotParam,
  Group,
  PdfParser,
  SearchMethod,
  Tenant,
} from "@/orval/models/administrator-api";

import { BotTemplateList } from "./BotTemplateList";
import { ConfirmCreateBot } from "./ConfirmCreateBot";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  tenant: Tenant;
  groups: Group[];
};

const getDefaultPdfParser = (
  enableDocumentIntelligence: boolean,
  enableLLMDocumentReader: boolean,
  templatePdfParser: PdfParser,
): PdfParser => {
  if (enableLLMDocumentReader && templatePdfParser === PdfParser.llm_document_reader) {
    return PdfParser.llm_document_reader;
  }
  if (enableDocumentIntelligence && templatePdfParser === PdfParser.document_intelligence) {
    return PdfParser.document_intelligence;
  }

  return PdfParser.pypdf;
};

export const convertBotTemplateToCreateBotParams = (
  selectedBotTemplate: BotTemplate,
  tenant: Tenant,
): CreateBotParam => {
  const allowedTextGenerationModelFamilies = getTextGenerationModelFamiliesFromAllowedModelFamilies(
    tenant.allowed_model_families,
  );
  return {
    name: selectedBotTemplate.name,
    description: selectedBotTemplate.description,
    example_questions: [""],
    approach: selectedBotTemplate.approach,
    search_method:
      selectedBotTemplate.approach === Approach.neollm ? SearchMethod.semantic_hybrid : undefined,
    response_generator_model_family:
      allowedTextGenerationModelFamilies.find(mf => mf === selectedBotTemplate.model_family) ||
      allowedTextGenerationModelFamilies[0],
    approach_variables: [
      {
        name: "document_limit",
        value: selectedBotTemplate.document_limit.toString(),
      },
      {
        name: "response_system_prompt",
        value: selectedBotTemplate.system_prompt,
      },
    ],
    enable_web_browsing: selectedBotTemplate.enable_web_browsing,
    enable_follow_up_questions: selectedBotTemplate.enable_follow_up_questions,
    pdf_parser: getDefaultPdfParser(
      tenant.enable_document_intelligence,
      tenant.enable_llm_document_reader,
      selectedBotTemplate.pdf_parser,
    ),
    icon_color: selectedBotTemplate.icon_color,
  };
};

export const CreateBotFromTemplateDialog = ({ open, onClose, refetch, tenant, groups }: Props) => {
  const [activeStep, setActiveStep] = useState<number>(0);
  const [selectedBotTemplate, setSelectedBotTemplate] = useState<BotTemplate>();
  const [selectedGroup, setSelectedGroup] = useState<Group>();

  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const handleNext = () => {
    if (activeStep >= 1) {
      return;
    }
    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    if (activeStep <= 0) {
      return;
    }
    setActiveStep(prev => prev - 1);
  };

  const handleSelectTemplate = (template: BotTemplate) => {
    setSelectedBotTemplate(template);
    handleNext();
  };

  const { data, isValidating: isLoadingGetBotTemplates } = useGetBotTemplates();
  const botTemplates = data?.bot_templates ?? [];

  const [{ loading: isLoadingCreateBot }, handleCreateBot] = useAsyncFn(
    async ({ botTemplate, group }: { botTemplate: BotTemplate; group: Group }) => {
      try {
        await createBot(
          tenant.id,
          group.id,
          convertBotTemplateToCreateBotParams(botTemplate, tenant),
        );
        refetch();
        enqueueSuccessSnackbar({ message: "ボットの作成に成功しました" });
        handleClose();
      } catch (e) {
        enqueueErrorSnackbar({ message: getErrorMessage(e) || "ボットの作成に失敗しました" });
      }
    },
  );

  const handleClose = () => {
    onClose();
    setSelectedBotTemplate(undefined);
    setActiveStep(0);
  };

  return (
    <CustomDialog
      open={open}
      onClose={handleClose}
      title="テンプレートから作成"
      maxWidth="lg"
      titleActions={
        <IconButton onClick={handleClose}>
          <CancelOutlinedIcon />
        </IconButton>
      }
      minHeight={600}
    >
      {activeStep === 0 && (
        <CustomDialogContent>
          {isLoadingGetBotTemplates ? (
            <CircularLoading />
          ) : (
            <Box sx={{ overflowY: "auto", maxHeight: "600px" }}>
              <BotTemplateList templates={botTemplates} onSelect={handleSelectTemplate} />
            </Box>
          )}
        </CustomDialogContent>
      )}
      {activeStep === 1 && selectedBotTemplate && (
        <>
          <CustomDialogContent>
            <Stack>
              <CustomLabel label="所属グループ" required />
              <Autocomplete<Group, false, true>
                options={groups}
                getOptionLabel={option => option.name}
                disableClearable
                fullWidth
                size="small"
                renderInput={params => <TextField {...params} size="small" />}
                value={selectedGroup}
                onChange={(_, value) => setSelectedGroup(value)}
              />
            </Stack>
            <Spacer px={20} />
            <ConfirmCreateBot
              createBotParams={convertBotTemplateToCreateBotParams(selectedBotTemplate, tenant)}
              iconUrl={selectedBotTemplate.icon_url || null}
              tenantName={tenant.name}
              allowedModelFamilies={tenant.allowed_model_families}
            />
          </CustomDialogContent>
          <DialogActions sx={{ px: 3, py: 2 }}>
            <Stack direction="row" gap={2}>
              <Button variant="outlined" onClick={handleBack} disabled={isLoadingCreateBot}>
                戻る
              </Button>
              <PrimaryButton
                text="作成"
                onClick={() =>
                  selectedGroup &&
                  handleCreateBot({
                    botTemplate: selectedBotTemplate,
                    group: selectedGroup,
                  })
                }
                loading={isLoadingCreateBot}
                disabled={!selectedGroup}
              />
            </Stack>
          </DialogActions>
        </>
      )}
    </CustomDialog>
  );
};
