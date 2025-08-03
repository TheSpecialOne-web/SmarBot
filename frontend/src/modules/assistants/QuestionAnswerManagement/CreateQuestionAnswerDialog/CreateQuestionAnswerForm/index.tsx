import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { Spacer } from "@/components/spacers/Spacer";
import { CreateQuestionAnswerParam } from "@/orval/models/backend-api";

type Props = {
  onSubmit: (params: CreateQuestionAnswerParam) => Promise<void>;
  onClose: () => void;
};

export const CreateQuestionAnswerForm = ({ onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<CreateQuestionAnswerParam>();

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <CustomTextField
          name="question"
          label="質問"
          fullWidth
          variant="outlined"
          control={control}
          rules={{ required: "質問は必須です" }}
        />

        <Spacer px={14} />

        <CustomTextField
          name="answer"
          label="回答"
          fullWidth
          variant="outlined"
          multiline
          rows={12}
          control={control}
          rules={{ required: "回答は必須です" }}
        />
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="追加" />
    </form>
  );
};
