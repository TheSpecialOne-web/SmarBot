import { Stack } from "@mui/material";
import { useFormContext } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { PromptTemplateProps } from "@/orval/models/backend-api";

type Props = {
  onSubmit: (params: PromptTemplateProps) => void;
  onClose: () => void;
  submitButtonText: string;
};

export const PromptTemplateForm = ({ onSubmit, onClose, submitButtonText }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useFormContext<PromptTemplateProps>();

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
