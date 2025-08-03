import { Typography } from "@mui/material";
import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { Spacer } from "@/components/spacers/Spacer";
import {
  CommonDocumentTemplate,
  UpdateCommonDocumentTemplateParam,
} from "@/orval/models/administrator-api";

type Props = {
  document: CommonDocumentTemplate;
  onSubmit: (params: UpdateCommonDocumentTemplateParam) => void;
  onClose: () => void;
};

export const UpdateCommonDocumentTemplateForm = ({ document, onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<UpdateCommonDocumentTemplateParam>({
    defaultValues: {
      memo: document.memo,
    },
  });

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <Typography variant="h4">{document.blob_name}</Typography>

        <Spacer px={14} />

        <CustomTextField
          control={control}
          label="メモ"
          name="memo"
          autoFocus
          fullWidth
          type="text"
        />
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="保存" loading={isSubmitting} />
    </form>
  );
};
