import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { Spacer } from "@/components/spacers/Spacer";
import { QuestionAnswer, UpdateQuestionAnswerParam } from "@/orval/models/backend-api";

type Props = {
  questionAnswer: QuestionAnswer;
  onSubmit: (params: UpdateQuestionAnswerParam) => Promise<void>;
  onClose: () => void;
};

export const UpdateQuestionAnswerForm = ({ questionAnswer, onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<UpdateQuestionAnswerParam>({
    defaultValues: {
      question: questionAnswer.question,
      answer: questionAnswer.answer,
    },
  });

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
      <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="保存" />
    </form>
  );
};
