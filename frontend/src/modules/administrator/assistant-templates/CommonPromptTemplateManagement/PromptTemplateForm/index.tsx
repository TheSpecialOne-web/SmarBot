import { Stack } from "@mui/material";
import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import {
  CreateCommonPromptTemplateParam,
  UpdateCommonPromptTemplateParam,
} from "@/orval/models/administrator-api";

type Props = {
  onSubmit: (params: CreateCommonPromptTemplateParam | UpdateCommonPromptTemplateParam) => void;
  onClose: () => void;
  submitButtonText: string;
  commonPromptTemplate?: CreateCommonPromptTemplateParam | UpdateCommonPromptTemplateParam;
};

export const PromptTemplateForm = ({
  onSubmit,
  onClose,
  submitButtonText,
  commonPromptTemplate,
}: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<CreateCommonPromptTemplateParam | UpdateCommonPromptTemplateParam>({
    defaultValues: commonPromptTemplate,
  });

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <Stack gap={2}>
          <CustomTextField
            name="title"
            label="タイトル"
            fullWidth
            variant="outlined"
            control={control}
            rules={{ required: "タイトルは必須です" }}
          />
          <CustomTextField
            name="prompt"
            label="質問"
            fullWidth
            variant="outlined"
            multiline
            rows={12}
            control={control}
            rules={{ required: "質問は必須です" }}
          />
        </Stack>
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText={submitButtonText} />
    </form>
  );
};
