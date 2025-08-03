import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { DocumentFolder, UpdateDocumentFolderParam } from "@/orval/models/backend-api";

type Props = {
  documentFolder: DocumentFolder;
  onSubmit: (params: UpdateDocumentFolderParam) => void;
  onClose: () => void;
};

export const UpdateDocumentFolderForm = ({ documentFolder, onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<UpdateDocumentFolderParam>({
    defaultValues: {
      name: documentFolder.name,
    },
  });

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <CustomTextField
          control={control}
          rules={{ required: "フォルダ名を入力してください" }}
          label="フォルダ名"
          name="name"
          autoFocus
          fullWidth
          type="text"
        />
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="保存" loading={isSubmitting} />
    </form>
  );
};
